import random
import threading
import time
from typing import Any


class DRLBridge:
    """
    DRL = Dynamic Runtime Layer (network distortion / link perturbation).

    Simulates an adversarial network between nodes:
    - packet loss   (messages silently dropped)
    - latency jitter (non-deterministic delay)
    - reordering    (FIFO not guaranteed)
    - duplication   (same message delivered multiple times)

    All parameters are configurable; the defaults represent a
    "noisy but functional" LAN (≈ 5% loss, 30 ms ± 15 ms jitter).
    """

    def __init__(
        self,
        node_id: str,
        loss_rate: float = 0.05,
        delay_mean: float = 0.030,
        delay_std: float = 0.015,
        reorder_prob: float = 0.0,
        dup_prob: float = 0.0,
    ):
        self.node_id = node_id
        self.loss_rate = loss_rate
        self.delay_mean = delay_mean
        self.delay_std = delay_std
        self.reorder_prob = reorder_prob
        self.dup_prob = dup_prob
        self._lock = threading.Lock()
        self._stats = {"sent": 0, "dropped": 0, "duplicated": 0, "delayed": 0}

    def send(self, msg: Any, target: str | None = None) -> Any | None:
        """
        Attempt to send `msg` across the (simulated) network.

        Returns:
            msg          — message delivered successfully
            None         — message was dropped (loss)
            [msg, msg]   — message was duplicated (returns list)

        The caller should treat None as "no ack" and handle retransmission.
        """
        with self._lock:
            self._stats["sent"] += 1

        # ── 1. Packet loss ─────────────────────────────────────────────
        if random.random() < self.loss_rate:
            with self._lock:
                self._stats["dropped"] += 1
            return None

        # ── 2. Duplication ─────────────────────────────────────────────
        duplicated = random.random() < self.dup_prob

        # ── 3. Latency jitter (non-blocking sleep in caller thread) ────
        delay = max(0, random.gauss(self.delay_mean, self.delay_std))
        if delay > 0:
            time.sleep(delay)
            with self._lock:
                self._stats["delayed"] += 1

        # ── 4. Reordering: handled by receiver buffer (stub for now) ───

        if duplicated:
            with self._lock:
                self._stats["duplicated"] += 1
            return [msg, msg]

        return msg

    def stats(self) -> dict:
        with self._lock:
            return dict(self._stats)

    def set_loss_rate(self, rate: float):
        with self._lock:
            self.loss_rate = max(0.0, min(1.0, rate))

    def set_delay(self, mean: float, std: float = 0.0):
        with self._lock:
            self.delay_mean = max(0, mean)
            self.delay_std = max(0, std)
