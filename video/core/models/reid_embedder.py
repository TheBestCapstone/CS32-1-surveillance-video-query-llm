"""行人 Re-ID 特征提取器。

默认使用 torchreid 的 OSNet x0_5（CNN，轻量高效）；若不可用则回退 torchvision MobileNetV2。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

_REID_INPUT_SIZE = (256, 128)  # (H, W)

try:
    from torchreid.reid import models as _torchreid_models
    _HAS_TORCHREID = True
except ImportError:
    _HAS_TORCHREID = False


class ReIDEmbedder:
    """封装 Re-ID 推理，对外暴露 embed_crops / cosine_similarity。

    backend:
        "torchreid_osnet" — torchreid OSNet x0_5（默认）
        "torchvision"     — MobileNetV2 (ImageNet)
    """

    def __init__(
        self,
        config_file: str | Path | None = None,
        weights: str | Path | None = None,
        device: str = "cpu",
        input_size: tuple[int, int] = _REID_INPUT_SIZE,
        backend: str | None = None,
    ) -> None:
        self.device = device
        self.input_size = input_size  # (H, W)
        self._backend = self._resolve_backend(backend, config_file, weights)
        self._model = self._load_model(config_file, weights, device)

    # ------------------------------------------------------------------
    # Backend resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_backend(
        backend: str | None,
        config_file: str | Path | None,
        weights: str | Path | None,
    ) -> str:
        if backend is not None:
            return backend
        if _HAS_TORCHREID:
            return "torchreid_osnet"
        return "torchvision"

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(
        self,
        config_file: str | Path | None,
        weights: str | Path | None,
        device: str,
    ) -> torch.nn.Module:
        if self._backend == "torchreid_osnet":
            return self._load_torchreid_osnet(device)
        return self._load_torchvision(device)

    @staticmethod
    def _load_torchreid_osnet(device: str) -> torch.nn.Module:
        model = _torchreid_models.build_model(
            name="osnet_x0_5",
            num_classes=1000,
            pretrained=True,
            use_gpu=False,
        )
        model.to(device)
        model.eval()
        logger.info("torchreid OSNet x0_5 loaded")
        return model

    @staticmethod
    def _load_torchvision(device: str) -> torch.nn.Module:
        from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

        base = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V2)
        # 去掉分类头，保留 features + global avg pool → 1280-d
        model = torch.nn.Sequential(
            base.features,
            torch.nn.AdaptiveAvgPool2d((1, 1)),
            torch.nn.Flatten(),
        )
        model.to(device)
        model.eval()
        logger.info("Torchvision MobileNetV2 fallback loaded (1280-d features)")
        return model

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    def _preprocess(self, imgs: Sequence[np.ndarray]) -> torch.Tensor:
        """BGR ndarray list -> (N, 3, H, W) float32 tensor (按照 backend 预处理)。"""
        tensors: list[torch.Tensor] = []
        h, w = self.input_size
        for img in imgs:
            rgb = img[:, :, ::-1].copy()
            resized = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_CUBIC)
            t = torch.as_tensor(resized.astype("float32").transpose(2, 0, 1))
            if self._backend == "torchvision":
                t = t / 255.0
                t = torch.stack(
                    [
                        (t[0] - 0.485) / 0.229,
                        (t[1] - 0.456) / 0.224,
                        (t[2] - 0.406) / 0.225,
                    ]
                )
            elif self._backend == "torchreid_osnet":
                t = t / 255.0
                t = torch.stack(
                    [
                        (t[0] - 0.485) / 0.229,
                        (t[1] - 0.456) / 0.224,
                        (t[2] - 0.406) / 0.225,
                    ]
                )
            tensors.append(t)
        return torch.stack(tensors)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @torch.no_grad()
    def embed_crops(self, crops: list[np.ndarray], batch_size: int = 64) -> np.ndarray:
        """批量提取特征，返回 (N, dim) L2-归一化向量。"""
        if not crops:
            return np.empty((0, 0), dtype=np.float32)

        all_feats: list[torch.Tensor] = []
        for i in range(0, len(crops), batch_size):
            batch = crops[i : i + batch_size]
            inp = self._preprocess(batch).to(self.device)
            feats = self._model(inp)
            feats = F.normalize(feats, dim=1)
            all_feats.append(feats.cpu())

        return torch.cat(all_feats, dim=0).numpy()

    @staticmethod
    def cosine_similarity(feats_a: np.ndarray, feats_b: np.ndarray) -> np.ndarray:
        """(Na, dim) x (Nb, dim) -> (Na, Nb) 余弦相似度矩阵。"""
        return feats_a @ feats_b.T
