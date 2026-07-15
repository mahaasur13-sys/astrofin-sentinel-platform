"""
Backpressure System — GPU saturation control + queue throttling.
Implements: load shedding, admission control, saturation monitoring.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import threading


@dataclass
class BackpressureConfig:
    """Configuration for backpressure thresholds."""
    gpu_saturation_max: float = 0.90        # Reject new jobs at 90% GPU VRAM
    gpu_saturation_warn: float = 0.75       # Warning at 75%
    queue_depth_max: int = 100              # Max jobs in queue
    queue_depth_warn: int = 50              # Warning threshold
    vram_reserve_mb: int = 512              # Reserved VRAM for system (512MB)
    eviction_threshold: float = 0.95         # Start evicting at 95%
    cooldown_seconds: int = 30              # Cooldown after backpressure trigger


@dataclass
class BackpressureStatus:
    """Current backpressure state."""
    gpu_saturation: float = 0.0
    gpu_vram_used_mb: int = 0
    gpu_vram_available_mb: int = 10240
    queue_depth: int = 0
    is_admitting: bool = True
    is_throttling: bool = False
    throttle_reason: str = ""
    last_triggered_at: Optional[str] = None
    cooldown_remaining_seconds: int = 0


class BackpressureSystem:
    """
    GPU saturation + queue admission control.

    Rules:
    1. GPU VRAM > config.gpu_saturation_max → stop admitting new GPU jobs
    2. Queue depth > config.queue_depth_max → stop admitting
    3. Backpressure triggered → cooldown before re-enabling
    4. System monitors saturation in real-time
    """

    def __init__(self, config: Optional[BackpressureConfig] = None):
        self.config = config or BackpressureConfig()
        self._lock = threading.RLock()
        self._last_triggered: Optional[datetime] = None
        self._gpu_vram_used_mb: int = 0
        self._gpu_vram_available_mb: int = 10240  # RTX 3060: ~10GB

    def get_status(self) -> BackpressureStatus:
        """Get current backpressure status."""
        with self._lock:
            cooldown_remaining = 0
            if self._last_triggered:
                elapsed = (datetime.now(timezone.utc) - self._last_triggered).total_seconds()
                cooldown_remaining = max(0, self.config.cooldown_seconds - int(elapsed))

            saturation = self._gpu_vram_used_mb / self._gpu_vram_available_mb if self._gpu_vram_available_mb > 0 else 0

            is_throttling = (saturation > self.config.gpu_saturation_max) or (cooldown_remaining > 0)

            return BackpressureStatus(
                gpu_saturation=saturation,
                gpu_vram_used_mb=self._gpu_vram_used_mb,
                gpu_vram_available_mb=self._gpu_vram_available_mb,
                queue_depth=0,  # Will be set by update_queue_depth
                is_admitting=not is_throttling,
                is_throttling=is_throttling,
                throttle_reason=self._get_reason(saturation, cooldown_remaining),
                last_triggered_at=self._last_triggered.isoformat() if self._last_triggered else None,
                cooldown_remaining_seconds=cooldown_remaining,
            )

    def should_admit(self, job_vram_mb: int, job_priority: int = 5) -> tuple[bool, str]:
        """
        Decide if a job should be admitted.
        Returns (admit: bool, reason: str)
        """
        with self._lock:
            status = self.get_status()

            # Check cooldown
            if status.cooldown_remaining_seconds > 0:
                return False, f"Cooldown: {status.cooldown_remaining_seconds}s remaining"

            # Check GPU saturation
            post_saturation = (self._gpu_vram_used_mb + job_vram_mb) / self._gpu_vram_available_mb
            if post_saturation > self.config.gpu_saturation_max:
                self._trigger_backpressure(f"GPU would be at {post_saturation:.0%}")
                return False, f"GPU saturation would exceed {self.config.gpu_saturation_max:.0%}"

            # Check if job fits in available VRAM
            available_vram = self._gpu_vram_available_mb - self._gpu_vram_used_mb - self.config.vram_reserve_mb
            if job_vram_mb > available_vram:
                self._trigger_backpressure(f"Job needs {job_vram_mb}MB, only {available_vram}MB available")
                return False, f"VRAM: need {job_vram_mb}MB, have {available_vram}MB"

            # High priority jobs can bypass some warnings (but not hard limits)
            if job_priority <= 1:  # Critical priority
                return True, "Admitted (critical priority)"

            return True, "Admitted"

    def record_job_start(self, job_vram_mb: int):
        """Record that a job started using VRAM."""
        with self._lock:
            self._gpu_vram_used_mb += job_vram_mb

    def record_job_complete(self, job_vram_mb: int):
        """Record that a job completed and released VRAM."""
        with self._lock:
            self._gpu_vram_used_mb = max(0, self._gpu_vram_used_mb - job_vram_mb)

    def update_queue_depth(self, depth: int):
        """Update current queue depth (called by queue manager)."""
        with self._lock:
            if depth > self.config.queue_depth_max:
                self._trigger_backpressure(f"Queue depth {depth} > {self.config.queue_depth_max}")

    def update_gpu_vram(self, used_mb: int, available_mb: int):
        """Update GPU VRAM stats (called from nvidia-smi or K8s metrics)."""
        with self._lock:
            self._gpu_vram_used_mb = used_mb
            self._gpu_vram_available_mb = available_mb

    def _trigger_backpressure(self, reason: str):
        """Trigger backpressure mode."""
        self._last_triggered = datetime.now(timezone.utc)

    def _get_reason(self, saturation: float, cooldown_remaining: int) -> str:
        if cooldown_remaining > 0:
            return f"Cooldown active: {cooldown_remaining}s"
        if saturation > self.config.gpu_saturation_max:
            return f"GPU saturation {saturation:.0%} > {self.config.gpu_saturation_max:.0%}"
        if saturation > self.config.gpu_saturation_warn:
            return f"GPU warning: {saturation:.0%}"
        return "OK"
