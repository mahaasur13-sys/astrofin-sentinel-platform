#!/usr/bin/env python3
"""
Labeling Functions — converts raw events to ML labels.
Failure: node goes down within horizon
Load: queue/GPU exceeds threshold within horizon
"""

import pandas as pd


def label_failure(
    df: pd.DataFrame,
    horizon_minutes: int = 30,
    failure_event_type: str = "NODE_DOWN",
) -> pd.Series:
    """
    Label failure events: 1 if node went down within horizon, 0 otherwise.
    """
    if df.empty or "event_type" not in df.columns:
        return pd.Series([0], index=df.index) if not df.empty else pd.Series(dtype=int)

    return (df["event_type"] == failure_event_type).astype(int)


def label_load_exceeded(
    df: pd.DataFrame,
    queue_threshold: float = 10.0,
    gpu_threshold: float = 0.95,
    horizon_minutes: int = 15,
) -> pd.Series:
    """
    Label load overrun: 1 if queue_depth or GPU util exceeded threshold within horizon.
    """
    if df.empty:
        return pd.Series(dtype=int)

    queue_exceeded = df.get("queue_depth", pd.Series([0] * len(df))) > queue_threshold
    gpu_exceeded = df.get("gpu_util", pd.Series([0.0] * len(df))) > gpu_threshold
    return (queue_exceeded | gpu_exceeded).astype(int)


def label_from_job_outcome(
    df: pd.DataFrame,
    failure_states: list | None = None,
) -> pd.Series:
    """
    Label from job outcome stored in job_events table.
    """
    if failure_states is None:
        failure_states = ["FAILED", "CANCELLED", "TIMEOUT"]

    if df.empty or "job_state" not in df.columns:
        return pd.Series([0], index=df.index) if not df.empty else pd.Series(dtype=int)

    return df["job_state"].isin(failure_states).astype(int)


def rolling_label(
    series: pd.Series,
    horizon: int,
    func: str = "max",
) -> pd.Series:
    """
    Apply rolling label: look ahead `horizon` rows and compute aggregate.
    """
    if func == "max":
        return series.rolling(window=horizon, min_periods=1).max().shift(-horizon)
    if func == "mean":
        return series.rolling(window=horizon, min_periods=1).mean().shift(-horizon)
    if func == "sum":
        return series.rolling(window=horizon, min_periods=1).sum().shift(-horizon)
    return series.shift(-horizon)


class LabelEngine:
    """Stub — implement labeling logic using label_* functions above."""

    pass
