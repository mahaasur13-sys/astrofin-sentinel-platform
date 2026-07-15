"""ATOM Operator — watches ATOMCluster CRDs, runs reconciliation loop."""

from __future__ import annotations

import logging
import os
import threading
import time

from kubernetes.client.rest import ApiException

from .client import K8sClient
from .reconciler import Reconciler

logger = logging.getLogger("atom.operator.controller")


class ATOMController:
    """
    Runs one background reconciliation thread per ATOMCluster.

    Thread map: {cluster_name → threading.Thread}
    """

    def __init__(self, k8s: K8sClient, poll_interval: float = 5.0):
        self.k8s = k8s
        self.poll_interval = poll_interval
        self.reconciler = Reconciler(k8s)
        self._threads: dict[str, threading.Thread] = {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        logger.info("ATOM Operator starting")
        watcher = threading.Thread(target=self._watch_loop, daemon=True)
        watcher.start()
        try:
            self._stop_event.wait()
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        logger.info("ATOM Operator shutting down")
        self._stop_event.set()
        for name, t in list(self._threads.items()):
            t.join(timeout=5)
        logger.info("ATOM Operator stopped")

    def _watch_loop(self) -> None:
        """
        List-watches all ATOMCluster resources in the target namespace.
        Spawns one reconciler thread per cluster.
        """
        namespace = os.environ.get("WATCH_NAMESPACE", "default")

        while not self._stop_event.is_set():
            try:
                clusters = self.k8s.list_clusters(namespace=namespace)
            except Exception as e:
                logger.error(f"Failed to list clusters: {e}")
                time.sleep(self.poll_interval)
                continue

            current_names = {c["metadata"]["name"] for c in clusters}
            with self._lock:
                # Start thread for new clusters
                for cluster in clusters:
                    name = cluster["metadata"]["name"]
                    if name not in self._threads or not self._threads[name].is_alive():
                        t = threading.Thread(
                            target=self._reconcile_loop,
                            args=(cluster,),
                            daemon=True,
                            name=f"reconciler-{name}",
                        )
                        self._threads[name] = t
                        t.start()
                        logger.info(f"Spawned reconciler thread for {name}")

                # Clean up stale threads
                dead = {
                    name: t for name, t in self._threads.items()
                    if name not in current_names or not t.is_alive()
                }
                for name in dead:
                    del self._threads[name]
                    logger.info(f"Removed reconciler thread for {name}")

            time.sleep(self.poll_interval)

    def _reconcile_loop(self, cluster: dict) -> None:
        """
        Continuous reconcile loop for one ATOMCluster.
        Runs until the cluster is deleted or operator shuts down.
        """
        name = cluster["metadata"]["name"]
        namespace = cluster["metadata"].get("namespace", "default")
        logger.info(f"[{name}] Reconciler loop started")

        while not self._stop_event.is_set():
            try:
                current = self.k8s.get_cluster(name, namespace)
                if current is None:
                    logger.info(f"[{name}] Cluster deleted — stopping reconciler")
                    break

                self.reconciler.reconcile(current)

            except ApiException as e:
                if e.status == 404:
                    logger.info(f"[{name}] Cluster gone — exit reconciler")
                    break
                logger.error(f"[{name}] API error: {e}")
            except Exception as e:
                logger.exception(f"[{name}] Unexpected error: {e}")

            time.sleep(self.poll_interval)

        logger.info(f"[{name}] Reconciler loop exited")
