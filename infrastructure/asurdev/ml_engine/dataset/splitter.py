#!/usr/bin/env python3
"""
Time-Aware Train/Val/Test Splitter.
CRITICAL: No future-leaking — strict temporal ordering preserved.
"""
import pandas as pd
from typing import Tuple


def time_aware_split(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    time_col: str = "time",
    group_col: str = "node_id",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset respecting temporal order (no future-leaking).
    Each node's timeline is split proportionally.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Ratios must sum to 1.0"

    df = df.sort_values(time_col)

    train_dfs, val_dfs, test_dfs = [], [], []

    for node_id, grp in df.groupby(group_col):
        n = len(grp)
        t = int(n * train_ratio)
        v = int(n * val_ratio)

        train_dfs.append(grp.iloc[:t])
        val_dfs.append(grp.iloc[t:t + v])
        test_dfs.append(grp.iloc[t + v:])

    train = pd.concat(train_dfs).sort_values(time_col)
    val = pd.concat(val_dfs).sort_values(time_col)
    test = pd.concat(test_dfs).sort_values(time_col)

    return train, val, test


def stratify_by_label(
    df: pd.DataFrame,
    label_col: str = "label_failure",
    min_positive_ratio: float = 0.05,
) -> pd.DataFrame:
    """
    Ensure label distribution is not too imbalanced.
    If positive class < min_positive_ratio, duplicate minority samples.
    """
    pos = df[df[label_col] == 1]
    neg = df[df[label_col] == 0]

    if len(pos) == 0:
        return df

    pos_ratio = len(pos) / len(df)
    if pos_ratio < min_positive_ratio and len(pos) < 1000:
        oversample_count = int((min_positive_ratio * len(df)) - len(pos))
        oversampled = pd.concat([pos] * max(1, oversample_count // len(pos) + 1)).iloc[:oversample_count]
        return pd.concat([neg, pos, oversampled]).sample(frac=1.0).reset_index(drop=True)

    return df
