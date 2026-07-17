"""GPU-aware scheduler — VRAM enforcement + priority decisions."""

from queue_manager.queue_manager import QueueManager


class GPUScheduler:
    """
    GPU-aware scheduling decisions.
    Uses VRAM tracking to decide which job gets the GPU.
    """

    # RTX 3060 safe VRAM limit (10.5 GB with overhead buffer)
    MAX_VRAM_MB = 10000
    OVERHEAD_MB = 500

    def __init__(self, queue_manager: QueueManager):
        self.queue = queue_manager
        self._vram_used_mb = 0

    def can_schedule(self, plan: dict) -> bool:
        """Check if plan fits in available VRAM."""
        vram_required = self._estimate_vram(plan)
        available = self.MAX_VRAM_MB - self.OVERHEAD_MB - self._vram_used_mb
        return vram_required <= available

    def estimate_vram_from_plan(self, plan: dict) -> int:
        """Estimate VRAM from DAG."""
        return self._estimate_vram(plan)

    def _estimate_vram(self, plan: dict) -> int:
        """Parse plan and estimate VRAM needs."""
        gpu_requested = plan.get("resources", {}).get("gpu_vram_mb", 0)
        if gpu_requested:
            return gpu_requested
        # Fallback: infer from task type
        task_type = plan.get("analysis", {}).get("type", "")
        if task_type in ("ml_training", "inference"):
            return 8000  # default ML VRAM
        if task_type == "data_processing":
            return 2000
        return 4000  # conservative default

    def should_preempt(self, running_job_id: str, new_plan: dict) -> bool:
        """Preempt lower-priority job if high-priority needs GPU."""
        running = self.queue.get_status(running_job_id)
        if not running:
            return False
        # Preempt if running job has lower priority number
        new_priority = new_plan.get("priority", 5)
        return running.priority > new_priority

    def release_vram(self, job_id: str):
        """Release VRAM when job completes."""
        # VRAM tracking is managed via queue completion
        pass

    def snapshot(self) -> dict:
        """Current GPU scheduler state."""
        return {
            "vram_used_mb": self._vram_used_mb,
            "vram_available_mb": self.MAX_VRAM_MB
            - self.OVERHEAD_MB
            - self._vram_used_mb,
            "gpu_busy": self.queue.is_gpu_busy,
            "queue_depth": self.queue.queue_depth,
        }
