"""trading/ledger/types.py — exact column types shared by SQLite (tests/fallback) and PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.types import TypeDecorator

# NUMERIC(38, 18) on PostgreSQL (exact). SQLite has no exact decimal type
# (NUMERIC affinity stores REAL → binary rounding), so there the value is stored
# as its canonical decimal string and parsed back into Decimal — no precision loss.
DECIMAL_PRECISION = 38
DECIMAL_SCALE = 18


def decimal_to_str(v: Decimal) -> str:
    """Canonical exact string (no context rounding: Decimal.normalize() would round to 28 digits)."""
    s = format(v, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class ExactDecimal(TypeDecorator):
    impl = Numeric(DECIMAL_PRECISION, DECIMAL_SCALE)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(64))
        return dialect.type_descriptor(Numeric(DECIMAL_PRECISION, DECIMAL_SCALE, asdecimal=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, Decimal) or isinstance(value, bool):
            raise TypeError(f"ExactDecimal requires Decimal, got {type(value).__name__}")
        if not value.is_finite():
            raise ValueError("ExactDecimal: non-finite value")
        exp = value.as_tuple().exponent
        if isinstance(exp, int) and -exp > DECIMAL_SCALE:
            raise ValueError(f"ExactDecimal: more than {DECIMAL_SCALE} fractional digits")
        if dialect.name == "sqlite":
            return decimal_to_str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(value) if not isinstance(value, Decimal) else value


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetime. Naive datetimes are refused on write."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
