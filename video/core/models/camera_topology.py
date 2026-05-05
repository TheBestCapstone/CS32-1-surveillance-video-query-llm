"""Camera Topology Prior: per-camera-pair transit time distribution.

Professional surveillance systems maintain a spatial-temporal graph of cameras:
  - Nodes  → individual cameras
  - Edges  → observed person transitions A → B
  - Weight → learned probability distribution over transit time Δt

This module:
  1. Records confirmed cross-camera transitions (Δt per directed pair).
  2. Fits a Gaussian Mixture Model when ≥ ``min_obs`` observations are available;
     falls back to a soft linear-decay prior for cold-start pairs.
  3. Exposes ``score(cam_a, cam_b, delta_t) → [0, 1]`` for use in the matching scorer.
  4. Can be persisted / loaded as JSON for reuse across sessions.

Usage in scoring
----------------
Old formula:  score = 0.70 * cosine + 0.30 * time_window_score(gap)
New formula:  score = 0.55 * cosine + 0.45 * topology_score(cam_a, cam_b, gap)

The topology score is topology-aware: for a cold cam pair it behaves like the old
linear decay; once ≥ 5 transitions have been observed it switches to normalized
GMM likelihood, rewarding gaps that fall within the empirically learned transit
window and penalising physically implausible gaps.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Campus Zone Map — Guide v2.0 (2026-05-04)
# Synthetic transit priors seed CameraTopologyPrior.observe_batch so matching
# uses zone-aware GMMs instead of cold-start linear decay.
# ---------------------------------------------------------------------------

_CAMPUS_ADMIN = frozenset({"G326", "G329"})
_CAMPUS_BUS = frozenset({"G505", "G506", "G508"})
_CAMPUS_SCHOOL = frozenset({
    "G299",
    "G328",
    "G330",
    "G336",
    "G339",
    "G419",
    "G420",
    "G421",
    "G423",
    "G424",
    "G638",
})
CAMERA_IDS_CAMPUS_GUIDE_V2: tuple[str, ...] = tuple(
    sorted(_CAMPUS_ADMIN | _CAMPUS_BUS | _CAMPUS_SCHOOL)
)


def campus_zone_of_camera(cam_id: str) -> str | None:
    """Return ``admin`` | ``bus`` | ``school`` for known guide IDs, else ``None``."""
    if cam_id in _CAMPUS_ADMIN:
        return "admin"
    if cam_id in _CAMPUS_BUS:
        return "bus"
    if cam_id in _CAMPUS_SCHOOL:
        return "school"
    return None


def _campus_pair_transit_range_sec(za: str, zb: str) -> tuple[float, float] | None:
    """Directed zones → plausible Δt window (seconds) from the zone map."""
    if za == zb:
        if za == "admin":
            return (10.0, 45.0)
        if za == "bus":
            return (30.0, 90.0)
        if za == "school":
            return (15.0, 90.0)
        return None
    zones = frozenset({za, zb})
    # ADMIN ↔ BUS: walking 15–60 s (diagram)
    if zones == frozenset({"admin", "bus"}):
        return (15.0, 60.0)
    # ADMIN / BUS ↔ SCHOOL (vertical campus legs; not explicit in ASCII → conservative)
    if zones == frozenset({"admin", "school"}):
        return (20.0, 120.0)
    if zones == frozenset({"bus", "school"}):
        return (30.0, 120.0)
    return None


# Minimum observations before fitting GMM instead of falling back to flat prior
_MIN_OBS_FOR_GMM = 5
# Number of GMM components (capped by available samples)
_GMM_MAX_COMPONENTS = 3
# Grid resolution for normalising GMM to [0, 1]
_NORM_GRID_POINTS = 500


class CameraTopologyPrior:
    """Spatial-temporal transition probability matrix across cameras.

    Parameters
    ----------
    cameras:
        Ordered list of camera identifiers (e.g. ``["cam1", "cam2", "cam3"]``).
    max_transit_sec:
        Hard cutoff: if Δt exceeds this value the score is always 0.
    n_bins:
        Number of histogram bins used for human-readable statistics.
    min_obs_for_gmm:
        Minimum confirmed transitions before fitting a GMM for a pair.
    """

    def __init__(
        self,
        cameras: list[str],
        max_transit_sec: float = 300.0,
        n_bins: int = 30,
        min_obs_for_gmm: int = _MIN_OBS_FOR_GMM,
    ) -> None:
        self.cameras = list(cameras)
        self.max_transit_sec = max_transit_sec
        self.n_bins = n_bins
        self.min_obs_for_gmm = min_obs_for_gmm

        # Raw observations per directed pair
        self._obs: dict[tuple[str, str], list[float]] = {}

        # Fitted GMM objects (lazy, refitted on new observations)
        self._gmm: dict[tuple[str, str], Any] = {}       # sklearn GaussianMixture
        self._gmm_max_density: dict[tuple[str, str], float] = {}

        # Whether pair has a valid fitted GMM
        self._fitted: set[tuple[str, str]] = set()

    # ------------------------------------------------------------------
    # Observation & fitting
    # ------------------------------------------------------------------

    def observe(self, cam_a: str, cam_b: str, delta_t: float) -> None:
        """Record one confirmed transition A → B with transit time ``delta_t``.

        Automatically re-fits the GMM when the count reaches a new multiple of
        ``min_obs_for_gmm`` (i.e. at 5, 10, 15 … observations).
        """
        if delta_t < 0 or delta_t > self.max_transit_sec:
            logger.debug(
                "Ignoring observation (%s→%s, Δt=%.1fs): outside [0, %.0f]",
                cam_a, cam_b, delta_t, self.max_transit_sec,
            )
            return
        pair = (cam_a, cam_b)
        self._obs.setdefault(pair, []).append(float(delta_t))
        n = len(self._obs[pair])
        if n >= self.min_obs_for_gmm and n % max(1, self.min_obs_for_gmm // 2) == 0:
            self._fit_gmm(cam_a, cam_b)

    def observe_batch(
        self, transitions: list[tuple[str, str, float]]
    ) -> None:
        """Bulk-record transitions from a list of (cam_a, cam_b, delta_t)."""
        # Insert raw observations without triggering per-item refit
        for cam_a, cam_b, delta_t in transitions:
            if 0 <= delta_t <= self.max_transit_sec:
                pair = (cam_a, cam_b)
                self._obs.setdefault(pair, []).append(float(delta_t))
        # Single refit pass after all observations
        pairs_seen: set[tuple[str, str]] = {(a, b) for a, b, _ in transitions}
        for pair in pairs_seen:
            if len(self._obs.get(pair, [])) >= self.min_obs_for_gmm:
                self._fit_gmm(*pair)

    def _fit_gmm(self, cam_a: str, cam_b: str) -> None:
        """Fit (or refit) a Gaussian Mixture Model for the pair (cam_a, cam_b)."""
        try:
            from sklearn.mixture import GaussianMixture
        except ImportError:
            logger.warning(
                "scikit-learn not available; topology prior will use flat decay."
            )
            return

        pair = (cam_a, cam_b)
        data = np.array(self._obs[pair], dtype=float).reshape(-1, 1)
        n_components = min(_GMM_MAX_COMPONENTS, max(1, len(data) // 3))
        gmm = GaussianMixture(
            n_components=n_components,
            covariance_type="full",
            random_state=42,
            n_init=3,
        )
        try:
            gmm.fit(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("GMM fit failed for %s→%s: %s", cam_a, cam_b, exc)
            return

        # Pre-compute normalisation constant
        grid = np.linspace(0.0, self.max_transit_sec, _NORM_GRID_POINTS).reshape(-1, 1)
        log_prob = gmm.score_samples(grid)
        max_density = float(np.exp(log_prob).max())
        if max_density <= 0:
            logger.warning("GMM for %s→%s has zero max density; skipping.", cam_a, cam_b)
            return

        self._gmm[pair] = gmm
        self._gmm_max_density[pair] = max_density
        self._fitted.add(pair)
        logger.debug(
            "GMM fitted for %s→%s: %d obs, %d components, max_density=%.4f",
            cam_a, cam_b, len(data), n_components, max_density,
        )

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(self, cam_a: str, cam_b: str, delta_t: float) -> float:
        """Topology score for a candidate pair (cam_a, cam_b) with gap ``delta_t``.

        Returns
        -------
        float in [0, 1]:
            * 0 if delta_t > max_transit_sec (hard cutoff).
            * Normalised GMM likelihood if pair has been fitted.
            * Soft linear decay (cold-start prior) otherwise.
        """
        if delta_t > self.max_transit_sec:
            return 0.0

        pair = (cam_a, cam_b)
        if pair in self._fitted:
            gmm = self._gmm[pair]
            max_density = self._gmm_max_density[pair]
            log_prob = gmm.score_samples(np.array([[delta_t]]))
            density = float(np.exp(log_prob[0]))
            return min(1.0, density / max_density)

        # Cold-start: soft linear decay + slight bonus for ≤30 s (corridor heuristic)
        if delta_t <= 30.0:
            return 1.0
        ratio = (delta_t - 30.0) / max(1.0, self.max_transit_sec - 30.0)
        return max(0.0, 1.0 - ratio)

    def expected_transit_sec(self, cam_a: str, cam_b: str) -> float | None:
        """Return the empirical mean transit time (None if no observations)."""
        obs = self._obs.get((cam_a, cam_b))
        if not obs:
            return None
        return float(np.mean(obs))

    # ------------------------------------------------------------------
    # Analytics / reporting
    # ------------------------------------------------------------------

    def transition_table(self) -> dict[str, dict[str, dict[str, Any]]]:
        """Return a human-readable nested dict summarising all directed pairs.

        Example output::

            {
              "cam1": {
                "cam2": {
                  "n_observations": 12,
                  "mean_transit_sec": 45.3,
                  "std_transit_sec": 8.1,
                  "fitted": true,
                  "gmm_components": 2,
                  "histogram": [0, 2, 5, 3, 2, 0]  # n_bins buckets
                }
              }
            }
        """
        table: dict[str, dict[str, dict[str, Any]]] = {}
        for cam_a in self.cameras:
            table[cam_a] = {}
            for cam_b in self.cameras:
                if cam_a == cam_b:
                    continue
                pair = (cam_a, cam_b)
                obs = self._obs.get(pair, [])
                entry: dict[str, Any] = {
                    "n_observations": len(obs),
                    "mean_transit_sec": float(np.mean(obs)) if obs else None,
                    "std_transit_sec": float(np.std(obs)) if obs else None,
                    "fitted": pair in self._fitted,
                }
                if pair in self._fitted:
                    entry["gmm_components"] = int(
                        self._gmm[pair].n_components  # type: ignore[attr-defined]
                    )
                if obs:
                    counts, _ = np.histogram(
                        obs,
                        bins=min(self.n_bins, len(obs)),
                        range=(0, self.max_transit_sec),
                    )
                    entry["histogram"] = counts.tolist()
                table[cam_a][cam_b] = entry
        return table

    def most_connected_pairs(self, top_k: int = 5) -> list[dict[str, Any]]:
        """Return the top-K directed pairs sorted by observation count."""
        rows = []
        for pair, obs in self._obs.items():
            rows.append({
                "cam_a": pair[0],
                "cam_b": pair[1],
                "n_observations": len(obs),
                "mean_transit_sec": float(np.mean(obs)) if obs else None,
                "fitted": pair in self._fitted,
            })
        rows.sort(key=lambda r: r["n_observations"], reverse=True)
        return rows[:top_k]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> Path:
        """Serialise observations (not the GMM — refitted on load) to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "cameras": self.cameras,
            "max_transit_sec": self.max_transit_sec,
            "n_bins": self.n_bins,
            "min_obs_for_gmm": self.min_obs_for_gmm,
            "observations": {
                f"{a}→{b}": obs
                for (a, b), obs in self._obs.items()
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("CameraTopologyPrior saved to %s", path)
        return path

    @classmethod
    def load(cls, path: str | Path) -> "CameraTopologyPrior":
        """Load observations from JSON and refit GMMs."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        obj = cls(
            cameras=data["cameras"],
            max_transit_sec=data.get("max_transit_sec", 300.0),
            n_bins=data.get("n_bins", 30),
            min_obs_for_gmm=data.get("min_obs_for_gmm", _MIN_OBS_FOR_GMM),
        )
        for key, obs in data.get("observations", {}).items():
            cam_a, cam_b = key.split("→", 1)
            obj._obs[(cam_a, cam_b)] = [float(v) for v in obs]
        # Refit GMMs
        for pair, obs in obj._obs.items():
            if len(obs) >= obj.min_obs_for_gmm:
                obj._fit_gmm(*pair)
        logger.info(
            "CameraTopologyPrior loaded from %s (%d pairs, %d fitted)",
            path, len(obj._obs), len(obj._fitted),
        )
        return obj

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_campus_guide_v2(
        cls,
        cameras: list[str] | None = None,
        *,
        logical_to_physical: dict[str, str] | None = None,
        samples_per_pair: int = 8,
        rng: np.random.Generator | None = None,
        max_transit_sec: float = 300.0,
        n_bins: int = 30,
        min_obs_for_gmm: int = _MIN_OBS_FOR_GMM,
    ) -> "CameraTopologyPrior":
        """Seed topology from the Campus Zone Map (Guide **v2.0 — 2026-05-04**).

        Zones::

            ADMIN:  G326, G329
            BUS:    G505, G506, G508
            SCHOOL: G299, G328, G330, G336, G339, G419, G420,
                    G421, G423, G424, G638

        Inter-zone walking windows follow the diagram (ADMIN↔BUS 15–60 s; BUS
        intra-zone 30–90 s; SCHOOL intra 15–90 s). ADMIN/BUS↔SCHOOL legs use
        conservative ranges because the drawing does not label seconds.

        Parameters
        ----------
        cameras:
            Pipeline camera ids to include. Default: all guide ids
            (:data:`CAMERA_IDS_CAMPUS_GUIDE_V2`).
        logical_to_physical:
            If tracks use aliases (e.g. ``cam1`` → ``G328``), map each logical
            id to a **physical** camera code so zone lookup succeeds; seeded
            observations are still stored under **logical** ids so
            ``score(logical_a, logical_b, Δt)`` matches the matcher.
        samples_per_pair:
            Uniform samples per directed pair inside the window (≥ ``min_obs_for_gmm``
            so GMM fits).
        rng:
            Optional NumPy Generator for reproducible synthetic Δt.

        Returns
        -------
        CameraTopologyPrior
            With synthetic observations fitted where zone pairs are known.
        """
        cam_list = (
            list(cameras)
            if cameras is not None
            else list(CAMERA_IDS_CAMPUS_GUIDE_V2)
        )
        rng = rng or np.random.default_rng(42)
        obj = cls(
            cameras=cam_list,
            max_transit_sec=max_transit_sec,
            n_bins=n_bins,
            min_obs_for_gmm=min_obs_for_gmm,
        )

        def zone_for(cid: str) -> str | None:
            phys = cid
            if logical_to_physical is not None and cid in logical_to_physical:
                phys = logical_to_physical[cid]
            return campus_zone_of_camera(phys)

        transitions: list[tuple[str, str, float]] = []
        for i, a in enumerate(cam_list):
            za = zone_for(a)
            if za is None:
                continue
            for b in cam_list[i + 1 :]:
                zb = zone_for(b)
                if zb is None:
                    continue
                tr_ab = _campus_pair_transit_range_sec(za, zb)
                if tr_ab is None:
                    continue
                lo_ab, hi_ab = tr_ab
                tr_ba = _campus_pair_transit_range_sec(zb, za)
                if tr_ba is None:
                    continue
                lo_ba, hi_ba = tr_ba
                for _ in range(samples_per_pair):
                    transitions.append((a, b, float(rng.uniform(lo_ab, hi_ab))))
                    transitions.append((b, a, float(rng.uniform(lo_ba, hi_ba))))

        obj.observe_batch(transitions)
        logger.info(
            "Campus guide v2.0: seeded %d synthetic transitions (%d directed pairs)",
            len(transitions),
            len(obj._obs),
        )
        return obj

    @classmethod
    def from_confirmed_matches(
        cls,
        matches: list[dict[str, Any]],
        cameras: list[str],
        max_transit_sec: float = 300.0,
    ) -> "CameraTopologyPrior":
        """Build topology prior from a list of confirmed global-entity appearances.

        Each item in ``matches`` should have the structure produced by
        ``GlobalEntity.appearances``::

            [
              {"camera_id": "cam1", "start_time": 10.0, "end_time": 15.0, ...},
              {"camera_id": "cam3", "start_time": 58.0, "end_time": 62.0, ...},
            ]

        The directed transition time is ``b.start_time - a.end_time`` for each
        consecutive appearance pair (sorted by start_time).
        """
        obj = cls(cameras=cameras, max_transit_sec=max_transit_sec)
        for entity_appearances in matches:
            sorted_apps = sorted(entity_appearances, key=lambda x: x["start_time"])
            for i in range(len(sorted_apps) - 1):
                a = sorted_apps[i]
                b = sorted_apps[i + 1]
                if a["camera_id"] == b["camera_id"]:
                    continue
                delta_t = float(b["start_time"]) - float(a["end_time"])
                obj.observe(a["camera_id"], b["camera_id"], delta_t)
        return obj

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # noqa: D105
        n_pairs = len(self._obs)
        n_fitted = len(self._fitted)
        total_obs = sum(len(v) for v in self._obs.values())
        return (
            f"CameraTopologyPrior(cameras={self.cameras!r}, "
            f"pairs={n_pairs}, fitted={n_fitted}, total_obs={total_obs})"
        )
