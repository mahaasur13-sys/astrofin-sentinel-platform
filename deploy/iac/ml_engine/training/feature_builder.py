#!/usr/bin/env python3
"""
Advanced feature engineering for failure prediction.
Adds rolling statistics, lags, time-based features.
"""

import numpy as np
import pandas as pd


def build_advanced_features(df: pd.DataFrame, horizon_minutes: int = 30) -> pd.DataFrame:
    """
    Adds sliding-window features, lag features, and temporal features.

    Args:
        df: Raw metrics DataFrame with at least: cpu_load, mem_usage, timestamp, failure
        horizon_minutes: Prediction horizon (used to set temporal context)

    Returns:
        DataFrame with engineered features added (NaN rows dropped)
    """
    df = df.copy()

    # Lag features (1 step back)
    df["cpu_load_lag1"] = df["cpu_load"].shift(1)
    df["mem_usage_lag1"] = df["mem_usage"].shift(1)
    if "gpu_util" in df.columns:
        df["gpu_util_lag1"] = df["gpu_util"].shift(1)
    if "disk_usage" in df.columns:
        df["disk_usage_lag1"] = df["disk_usage"].shift(1)

    # Rolling statistics (5-step window)
    df["cpu_load_rolling_mean_5"] = df["cpu_load"].rolling(5).mean()
    df["cpu_load_rolling_std_5"] = df["cpu_load"].rolling(5).std()
    df["mem_usage_rolling_mean_5"] = df["mem_usage"].rolling(5).mean()

    if "gpu_util" in df.columns:
        df["gpu_util_rolling_mean_5"] = df["gpu_util"].rolling(5).mean()
        df["gpu_util_rolling_std_5"] = df["gpu_util"].rolling(5).std()

    # Failure rate over previous hour (if failure label exists)
    if "failure" in df.columns or "label_failure" in df.columns:
        col = "label_failure" if "label_failure" in df.columns else "failure"
        df["failure_rate_prev_hour"] = df[col].rolling(60).mean()

    # Temporal features
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        df["hour_of_day"] = ts.dt.hour
        df["day_of_week"] = ts.dt.dayofweek
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["is_night"] = ((ts.dt.hour >= 22) | (ts.dt.hour <= 6)).astype(int)

    # Interaction features
    df["cpu_x_mem"] = df["cpu_load"] * df["mem_usage"]
    df["cpu_squared"] = df["cpu_load"] ** 2
    if "gpu_util" in df.columns:
        df["gpu_x_cpu"] = df["gpu_util"] * df["cpu_load"]

    # Trend features
    df["cpu_load_diff1"] = df["cpu_load"].diff(1)
    df["mem_usage_diff1"] = df["mem_usage"].diff(1)

    return df.dropna()


def add_rolling_features(df: pd.DataFrame, windows: list[int] = None) -> pd.DataFrame:
    """
    Add rolling mean/std features for configurable windows.
    """
    if windows is None:
        windows = [3, 5, 10, 30]

    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        for w in windows:
            df[f"{col}_rolling_mean_{w}"] = df[col].rolling(w).mean()
            df[f"{col}_rolling_std_{w}"] = df[col].rolling(w).std()

    return df.dropna()
