# HMMRegimeAgent

## Purpose

Использует скрытые марковские модели (HMM) для определения текущего рыночного режима (бычий, медвежий, флэт) и обнаружения рыночных аномалий на основе логарифмической вероятности (log-likelihood).

## Key Metrics

- **regime** (int): Текущее скрытое состояние (0=bull, 1=sideways, 2=bear).
- **regime_probabilities** (list[float]): Распределение вероятностей по состояниям.
- **log_likelihood** (float): Оценка того, насколько текущее поведение рынка соответствует изученной модели.
- **is_anomaly** (bool): Флаг резкого отклонения от нормы.

## Risk Management

- Если `is_anomaly == True`, агент возвращает `SignalDirection.AVOID` с высоким confidence (90).
- Risk Engine должен использовать `regime_probabilities` для динамической подстройки плеча и размера позиции.

## Confidence Rules

- Base confidence = `max(regime_probabilities) * 100`.
- Если данных недостаточно (< lookback периодов), confidence = 50, `data_quality` = 0.0.
- При аномалии confidence = 90 для сигнала AVOID.
