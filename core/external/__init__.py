# core/external/__init__.py
from core.external.circuit_breaker import CircuitBreaker, circuit_breaker
from core.external.coingecko_client import CoinGeckoClient
from core.external.ephemeris_client import EphemerisClient

__all__ = ["CircuitBreaker", "circuit_breaker", "CoinGeckoClient", "EphemerisClient"]
