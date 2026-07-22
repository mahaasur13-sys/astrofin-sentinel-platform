# ATOM-KARL-015 Phase 5 — Lag Window Integration

**Status:** ✅ Implemented
**Date:** 2026-03-29
**ATOMS:** KARL-015 Phase 5 (P2)

---

## Overview

Phase 5 adds two complementary mechanisms to the KARL control loop:

1. **Lag Window** (`lag_windowing.py`) — EMA-based confidence smoothing that reduces signal noise
2. **Risk Controller** (`risk_control.py`) — Dynamic position sizing based on `position_lag` metric

Both are gated by feature flags and are fully backward-compatible.

---

## 1. LagWindow — Signal Smoothing

### Purpose

Financial signals are inherently noisy. A single spike in agent confidence (e.g., 30→90) can distort decision-making. `LagWindow` applies EMA smoothing so that:
- **Warmup** (first 20 decisions): 30% weight on EMA, 70% on raw — adapts quickly
- **Mature** (after 20 decisions): 15% weight on EMA, 85% on raw — stable, noise-resistant

### Key Metrics

| Metric | Description |
|--------|-------------|
| `raw_confidence` | Original confidence from synthesis |
| `ema_confidence` | EMA of recent confidences |
| `lag_adjustment` | `(ema - raw) / raw` — negative when raw is a spike up |
| `position_lag` | Deviation of current position from its moving average |
| `window_mature` | `count >= 20` — enables risk control |

### Adaptive Window Sizing

Window size adapts to market volatility:

| Condition | Window Size | Effect |
|-----------|-------------|--------|
| `vol <= 0.005` (low) | `base × 1.5` (max 100) | More smoothing |
| `vol >= 0.02` (high) | `base ÷ 2` (min 20) | Faster reaction |
| Normal | `base = 50` | Balanced |

### How It Works

```
Raw Confidence (90) → LagWindow.add() → final_confidence (72)
                                        ├─ EMA smoothing (ema=68.4)
                                        ├─ lag_adj = (68.4-90)/90 = -0.24
                                        └─ position_lag computed from history
```

---

## 2. Risk Controller — Dynamic Position Sizing

### Purpose

Position sizing is static by default (e.g., always 2%). The risk controller adjusts position size based on `position_lag`:

| Condition | Action | Factor |
|-----------|--------|--------|
| `position_lag < -0.3` (overheat) | Reduce position | × 0.8 |
| `position_lag > +0.3` (undertrade) | Increase position | × 1.1 |
| Inside `[-0.3, +0.3]` | No change | — |

**Hard bounds:** `[0.01, 0.20]`

### Example

```
Current position: 0.10 (2%)
position_lag: 0.5 (position below its moving average → undertrading)
→ New position: 0.10 × 1.1 = 0.11 (2.2%)
```

Risk control only activates when the lag window is **mature** (≥20 decisions), preventing premature adjustments during the warmup phase.

---

## Integration in `karl_synthesis.py`

```
run() flow:
  Step 2  Base synthesis → confidence=90
  Step 3  SelfQ (optional)
  Step 4  Grounding adjustment
  Step 4b Lag Window smoothing → confidence=72 (smoothed)
           ├─ apply_position_lag_risk() if window_mature
           └─ lag_metrics stored in synth_dict["lag_metrics"]
  Step 5  Reward estimation (uses smoothed confidence)
  Step 7  DecisionRecord (uses smoothed confidence)
```

---

## Configuration via Environment Variables

```bash
# Lag Windowing
LAG_WINDOWING_ENABLED=true          # master switch
LAG_ADAPTIVE_WINDOW=true           # adaptive window sizing
LAG_BASE_WINDOW_SIZE=50            # EMA lookback (default)
LAG_MIN_WINDOW_SIZE=20             # minimum window
LAG_MAX_WINDOW_SIZE=100            # maximum window
LAG_BLEND_MATURE=0.15              # EMA weight after warmup

# Risk Control
RISK_USE_POSITION_LAG=true         # enable position sizing
RISK_POSITION_LAG_THRESHOLD=0.3    # trigger threshold
RISK_REDUCTION_FACTOR=0.8          # overheat multiplier
RISK_INCREASE_FACTOR=1.1          # undertrade multiplier
RISK_MIN_POSITION=0.01            # floor
RISK_MAX_POSITION=0.20            # ceiling
```

---

## Example Logs

### LagWindow Active (confidence smoothing)

```
[LagWindow] conf 90 → 72 (adj=-0.240, pos_lag=+0.150)
```

### Risk Control — Position Increased

```
[RiskControl] position adjusted: lag=+0.500 → 0.1100
```

### Risk Control — Position Reduced

```
[RiskControl] position adjusted: lag=-0.450 → 0.0160
```

### Disabled (warmup phase — no risk control)

```
[LagWindow] conf 88 → 83 (adj=-0.059, pos_lag=+0.020)
# No RiskControl log — window not mature yet
```

---

## Backward Compatibility

- `LAG_WINDOWING_ENABLED=false` → `_apply_lag_smoothing()` returns inputs unchanged
- `RISK_USE_POSITION_LAG=false` → `apply_position_lag_risk()` returns input unchanged
- All new fields (`lag_metrics`, `position_risk_adjusted`) are additive — no existing code breaks

---

## Files Changed / Created

| File | Change |
|------|--------|
| `agents/karl_synthesis.py` | ✅ Modified — imports, `__init__`, `_apply_lag_smoothing()`, integration in `run()` |
| `agents/_impl/amre/risk_control.py` | 🆕 New — `apply_position_lag_risk()` |
| `tests/test_karl_synthesis_lag.py` | 🆕 New — LagWindow integration tests |
| `tests/test_risk_control.py` | 🆕 New — risk controller unit tests |
| `agents/_impl/amre/test_lag_windowing.py` | ✅ Already existed — LagWindow unit tests |
| `.env.example` | ✅ Updated — Phase 5 env vars added |
| `docs/phase5_lag_window_integration.md` | 🆕 New — this document |

---

## Acceptance Criteria Checklist

- [x] `KARLSynthesisAgent` imports and initializes `LagWindow` via `get_lag_window()`
- [x] Method `_apply_lag_smoothing` implemented and covered by tests
- [x] Main decision loop passes confidence and position through `LagWindow`
- [x] `risk_control.py` created — `apply_position_lag_risk()` works correctly
- [x] Unit tests for `karl_synthesis_lag.py` and `test_risk_control.py` added
- [x] All tests pass
- [x] Feature flags correctly enable/disable new behavior
- [x] Documentation updated
