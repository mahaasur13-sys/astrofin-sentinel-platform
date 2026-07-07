#!/usr/bin/env python3
"""
Prometheus → TimescaleDB Ingester
Reads from Prometheus exporter HTTP endpoints, writes to TimescaleDB.
Supports: slurm_exporter, ceph_exporter, wg_exporter, dcgm_exporter, node_exporter.

Usage:
    python prometheus_collector.py --config config.yaml
"""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Event, Thread
from urllib.error import URLError
from urllib.request import urlopen

import psycopg2
import structlog
import yaml

logger = structlog.get_logger()

METRIC_RE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*){([^}]*)} (.+)$")
SIMPLE_RE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*) (.+)$")


@dataclass
class MetricPoint:
    timestamp: datetime
    metric: str
    node_id: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)


class TimescaleWriter:
    def __init__(self, dsn: str, batch_size: int = 500, flush_interval: float = 5.0):
        self.dsn = dsn
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer: list[MetricPoint] = []
        self.conn: psycopg2.extensions.connection | None = None
        self._connect()
        self._last_flush = time.monotonic()

    def _connect(self):
        self.conn = psycopg2.connect(self.dsn)
        self.conn.autocommit = False
        cur = self.conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
        self.conn.commit()
        logger.info("connected to TimescaleDB")

    def write(self, point: MetricPoint):
        self.buffer.append(point)
        if len(self.buffer) >= self.batch_size:
            self._flush()

    def _flush(self):
        if not self.buffer:
            return
        cur = self.conn.cursor()
        cur.executemany(
            "INSERT INTO metrics (time, node_id, metric, value, labels) VALUES (%s, %s, %s, %s, %s)",
            [(p.timestamp, p.node_id, p.metric, p.value, p.labels) for p in self.buffer],
        )
        self.conn.commit()
        logger.debug("flushed", count=len(self.buffer))
        self.buffer.clear()
        self._last_flush = time.monotonic()

    def periodic_flush(self):
        if time.monotonic() - self._last_flush >= self.flush_interval:
            self._flush()

    def close(self):
        self._flush()
        if self.conn:
            self.conn.close()


class PrometheusCollector:
    def __init__(self, writer: TimescaleWriter, scrape_interval: float = 15.0):
        self.writer = writer
        self.scrape_interval = scrape_interval
        self._stop = Event()
        self._threads: list[Thread] = []

    def parse_metrics(self, text: str, source_node: str) -> list[MetricPoint]:
        points = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = METRIC_RE.match(line)
            if m:
                metric, labels_str, value = m.groups()
                labels = dict(kv.split("=") for kv in labels_str.split(",") if "=" in kv)
                node_id = labels.pop("node", source_node)
            else:
                m = SIMPLE_RE.match(line)
                if not m:
                    continue
                metric, value = m.groups()
                labels = {}
                node_id = source_node
            try:
                value = float(value)
            except ValueError:
                continue
            points.append(
                MetricPoint(
                    timestamp=datetime.now(timezone.utc), metric=metric, node_id=node_id, value=value, labels=labels
                )
            )
        return points

    def scrape_exporter(self, url: str, node_id: str):
        try:
            with urlopen(url, timeout=10) as resp:
                text = resp.read().decode("utf-8")
            points = self.parse_metrics(text, node_id)
            for p in points:
                self.writer.write(p)
            logger.debug("scraped", node=node_id, url=url, points=len(points))
        except (URLError, TimeoutError) as e:
            logger.warning("scrape_failed", node=node_id, url=url, error=str(e))

    def _scrape_loop(self, url: str, node_id: str):
        while not self._stop.wait(self.scrape_interval):
            self.scrape_exporter(url, node_id)
            self.writer.periodic_flush()

    def add_exporter(self, url: str, node_id: str):
        t = Thread(target=self._scrape_loop, args=(url, node_id), daemon=True)
        self._threads.append(t)

    def start(self):
        for t in self._threads:
            t.start()
        logger.info("collector started", targets=len(self._threads))

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)
        self.writer.close()
        logger.info("collector stopped")


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    db_dsn = f"postgresql://{config['db']['user']}:{config['db']['password']}@{config['db']['host']}:{config['db']['port']}/{config['db']['database']}"
    writer = TimescaleWriter(db_dsn)
    collector = PrometheusCollector(writer)

    for target in config["targets"]:
        collector.add_exporter(target["url"], target["node_id"])

    collector.start()
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        collector.stop()
