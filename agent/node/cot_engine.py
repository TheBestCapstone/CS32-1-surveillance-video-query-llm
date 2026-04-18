import logging
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar("T")


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABORTED = "aborted"


class BranchType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class StepResult(Generic[T]):
    step_name: str
    status: StepStatus
    output: Optional[T] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_success(self) -> bool:
        return self.status == StepStatus.COMPLETED

    def is_failure(self) -> bool:
        return self.status in {StepStatus.FAILED, StepStatus.ABORTED}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class CoTContext:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_input: Any = None
    current_step: Optional[str] = None
    step_history: List[StepResult] = field(default_factory=list)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[str] = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_duration_ms: float = 0.0

    def add_step_result(self, result: StepResult) -> None:
        self.step_history.append(result)
        if result.output is not None:
            self.intermediate_results[result.step_name] = result.output

    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        for result in self.step_history:
            if result.step_name == step_name:
                return result
        return None

    def get_intermediate(self, step_name: str) -> Optional[Any]:
        return self.intermediate_results.get(step_name)
        
    def set_intermediate(self, key: str, value: Any) -> None:
        self.intermediate_results[key] = value

    def get_full_chain(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.step_history]

    def get_reasoning_trace(self) -> str:
        lines = [f"=== CoT Chain {self.id[:8]} ==="]
        lines.append(f"Input: {self.original_input}")
        lines.append(f"Status: {self.status.value}")
        lines.append("")
        for i, result in enumerate(self.step_history, 1):
            status_icon = "✓" if result.is_success() else "✗" if result.is_failure() else "○"
            lines.append(f"{i}. [{status_icon}] {result.step_name} ({result.duration_ms:.1f}ms)")
            if result.output:
                output_str = str(result.output)
                if len(output_str) > 100:
                    output_str = output_str[:100] + "..."
                lines.append(f"   Output: {output_str}")
            if result.error:
                lines.append(f"   Error: {result.error}")
        lines.append("")
        lines.append(f"Total duration: {self.total_duration_ms:.1f}ms")
        if self.completed_at:
            lines.append(f"Completed at: {self.completed_at}")
        return "\n".join(lines)

    def can_continue(self) -> bool:
        return self.status == StepStatus.PENDING or self.status == StepStatus.RUNNING

    def abort(self, reason: str = "Aborted by user") -> None:
        self.status = StepStatus.ABORTED
        self.completed_at = datetime.now().isoformat()


class CoTStep(ABC, Generic[T]):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, ctx: CoTContext) -> StepResult[T]:
        pass

    def should_skip(self, ctx: CoTContext) -> bool:
        return False

    def on_error(self, ctx: CoTContext, error: Exception) -> None:
        logger.error(f"[{self.name}] Step failed: {error}")


class SequentialCoTStep(CoTStep[T]):
    def __init__(self, name: str, handler: Callable[[CoTContext], T], description: str = ""):
        super().__init__(name, description)
        self.handler = handler

    def execute(self, ctx: CoTContext) -> StepResult[T]:
        try:
            output = self.handler(ctx)
            return StepResult(step_name=self.name, status=StepStatus.COMPLETED, output=output)
        except Exception as e:
            self.on_error(ctx, e)
            return StepResult(step_name=self.name, status=StepStatus.FAILED, error=str(e))


class CoTCondition:
    def __init__(self, name: str, checker: Callable[[CoTContext], bool]):
        self.name = name
        self.checker = checker

    def evaluate(self, ctx: CoTContext) -> bool:
        try:
            return self.checker(ctx)
        except Exception:
            return False


class ConditionalStep(CoTStep[Any]):
    def __init__(self, name: str, condition: CoTCondition, true_step: CoTStep, false_step: Optional[CoTStep] = None):
        super().__init__(name, f"Conditional: {condition.name}")
        self.condition = condition
        self.true_step = true_step
        self.false_step = false_step

    def execute(self, ctx: CoTContext) -> StepResult[Any]:
        condition_met = self.condition.evaluate(ctx)
        target_step = self.true_step if condition_met else self.false_step

        if target_step is None:
            return StepResult(step_name=self.name, status=StepStatus.SKIPPED, output={"condition": condition_met, "branch": "none"})

        branch_name = "true" if condition_met else "false"
        logger.info(f"[{self.name}] Condition '{self.condition.name}' = {condition_met}, branching to {target_step.name}")

        return target_step.execute(ctx)

    def should_skip(self, ctx: CoTContext) -> bool:
        return False


class ParallelBranch:
    def __init__(self, name: str, steps: List[CoTStep]):
        self.name = name
        self.steps = steps


class ParallelExecutionStep(CoTStep[List[StepResult]]):
    def __init__(self, name: str, branches: List[ParallelBranch], merge_handler: Optional[Callable[[List[StepResult]], Any]] = None):
        super().__init__(name, f"Parallel execution of {len(branches)} branches")
        self.branches = branches
        self.merge_handler = merge_handler

    def execute(self, ctx: CoTContext) -> StepResult[List[StepResult]]:
        all_results: List[StepResult] = []

        for branch in self.branches:
            logger.info(f"[{self.name}] Executing branch: {branch.name}")
            for step in branch.steps:
                if not step.should_skip(ctx):
                    result = step.execute(ctx)
                    all_results.append(result)
                    if result.is_failure():
                        logger.warning(f"[{self.name}] Step {step.name} failed in branch {branch.name}")
                else:
                    logger.info(f"[{self.name}] Step {step.name} skipped")

        merged_output = all_results
        if self.merge_handler:
            try:
                merged_output = self.merge_handler(all_results)
            except Exception as e:
                logger.error(f"[{self.name}] Merge handler failed: {e}")

        return StepResult(step_name=self.name, status=StepStatus.COMPLETED, output=merged_output, metadata={"branch_count": len(self.branches), "total_steps": len(all_results)})


class CoTEngine:
    def __init__(self, name: str = "CoTEngine"):
        self.name = name
        self.steps: List[CoTStep] = []
        self.step_registry: Dict[str, CoTStep] = {}
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: CoTStep) -> "CoTEngine":
        self.steps.append(step)
        self.step_registry[step.name] = step
        return self

    def add_sequential(self, name: str, handler: Callable[[CoTContext], T], description: str = "") -> "CoTEngine":
        step = SequentialCoTStep(name, handler, description)
        return self.add_step(step)

    def add_conditional(self, name: str, condition: CoTCondition, true_step: CoTStep, false_step: Optional[CoTStep] = None) -> "CoTEngine":
        step = ConditionalStep(name, condition, true_step, false_step)
        return self.add_step(step)

    def add_parallel(self, name: str, branches: List[ParallelBranch], merge_handler: Optional[Callable] = None) -> "CoTEngine":
        step = ParallelExecutionStep(name, branches, merge_handler)
        return self.add_step(step)

    def execute(self, input_data: Any, max_duration_ms: float = 30000.0) -> CoTContext:
        ctx = CoTContext(original_input=input_data, status=StepStatus.RUNNING)
        start_time = time.time()

        try:
            for step in self.steps:
                if not ctx.can_continue():
                    logger.info(f"[{self.name}] Context aborted, stopping execution")
                    break

                if step.should_skip(ctx):
                    logger.info(f"[{self.name}] Step {step.name} skipped by should_skip")
                    continue

                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms > max_duration_ms:
                    logger.warning(f"[{self.name}] Max duration {max_duration_ms}ms exceeded, aborting")
                    ctx.abort(f"Max duration exceeded: {elapsed_ms:.1f}ms")
                    break

                logger.info(f"[{self.name}] Executing step: {step.name}")
                ctx.current_step = step.name

                step_start = time.time()
                result = step.execute(ctx)
                step_duration = (time.time() - step_start) * 1000
                result.duration_ms = step_duration

                ctx.add_step_result(result)

                if result.is_failure() and not ctx.can_continue():
                    logger.warning(f"[{self.name}] Step {step.name} failed, aborting chain")
                    break

            if ctx.can_continue():
                ctx.status = StepStatus.COMPLETED
            elif ctx.status == StepStatus.RUNNING:
                ctx.status = StepStatus.COMPLETED

        except Exception as e:
            logger.error(f"[{self.name}] Unexpected error: {e}", exc_info=True)
            ctx.status = StepStatus.FAILED
            ctx.metadata["error"] = str(e)

        ctx.completed_at = datetime.now().isoformat()
        ctx.total_duration_ms = (time.time() - start_time) * 1000

        return ctx

    def get_step(self, name: str) -> Optional[CoTStep]:
        return self.step_registry.get(name)

    def replay(self, ctx: CoTContext) -> CoTContext:
        return self.execute(ctx.original_input)


def create_cot_engine(name: str, steps: List[CoTStep]) -> CoTEngine:
    engine = CoTEngine(name)
    for step in steps:
        engine.add_step(step)
    return engine


def log_step_result(result: StepResult) -> None:
    status_icon = "✓" if result.is_success() else "✗" if result.is_failure() else "○"
    logger.info(f"  [{status_icon}] {result.step_name}: {result.duration_ms:.1f}ms")
    if result.error:
        logger.error(f"      Error: {result.error}")


def log_context(ctx: CoTContext) -> None:
    logger.info(f"=== CoT Execution Summary: {ctx.id[:8]} ===")
    logger.info(f"  Status: {ctx.status.value}")
    logger.info(f"  Total duration: {ctx.total_duration_ms:.1f}ms")
    logger.info(f"  Steps executed: {len(ctx.step_history)}")
    for result in ctx.step_history:
        log_step_result(result)
