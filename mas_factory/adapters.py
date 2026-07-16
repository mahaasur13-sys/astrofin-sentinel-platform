"""mas_factory/adapters.py - Context adapters between agents"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MessageFormat:
    """Standard message format between agents"""

    sender: str
    recipient: str
    intent: str  # "request" | "response" | "query"
    payload: dict[str, Any]
    metadata: dict[str, Any]


class ContextAdapter:
    """Base class for context transformations"""

    def adapt(self, data: Any, context: dict[str, Any]) -> Any:
        raise NotImplementedError


class PassthroughAdapter(ContextAdapter):
    def adapt(self, data: Any, context: dict[str, Any]) -> Any:
        return data


class ExtractSignalAdapter(ContextAdapter):
    """Extract only signal fields from agent output"""

    def adapt(self, data: Any, context: dict[str, Any]) -> Any:
        if isinstance(data, dict):
            return {
                "agent_name": data.get("agent_name", "unknown"),
                "signal": data.get("signal", "NEUTRAL"),
                "confidence": data.get("confidence", 50),
                "reasoning": data.get("reasoning", ""),
            }
        return data


class MergeSignalsAdapter(ContextAdapter):
    """Merge multiple agent signals into consensus"""

    def adapt(self, data: list[Any], context: dict[str, Any]) -> Any:
        if not isinstance(data, list):
            return data

        signals = [d.get("signal", "NEUTRAL") for d in data if isinstance(d, dict)]
        confs = [d.get("confidence", 50) for d in data if isinstance(d, dict)]

        # Simple majority voting
        long_count = sum(1 for s in signals if s in ("LONG", "BUY"))
        short_count = sum(1 for s in signals if s in ("SHORT", "SELL"))

        if long_count > short_count:
            consensus = "LONG"
        elif short_count > long_count:
            consensus = "SHORT"
        else:
            consensus = "NEUTRAL"

        return {
            "consensus_signal": consensus,
            "confidence": sum(confs) / len(confs) if confs else 50,
            "agent_count": len(data),
            "diversity": len(set(signals)),
        }


class AggregateConfidenceAdapter(ContextAdapter):
    """Aggregate confidence scores from multiple agents"""

    def adapt(self, data: list[Any], context: dict[str, Any]) -> Any:
        if not isinstance(data, list):
            return {"confidence": 50, "count": 0}

        confs = [d.get("confidence", 50) for d in data if isinstance(d, dict)]

        # Weighted average based on agent weights in context
        weights = context.get("agent_weights", {})
        if weights:
            weighted_sum = sum(
                confs[i] * weights.get(data[i].get("agent_name", ""), 1.0)
                for i in range(len(data))
                if isinstance(data[i], dict)
            )
            total_weight = sum(weights.values())
            avg_conf = weighted_sum / total_weight if total_weight > 0 else sum(confs) / len(confs)
        else:
            avg_conf = sum(confs) / len(confs) if confs else 50

        return {
            "avg_confidence": avg_conf,
            "max_confidence": max(confs) if confs else 50,
            "min_confidence": min(confs) if confs else 50,
            "count": len(confs),
        }


class FilterByConfidenceAdapter(ContextAdapter):
    """Filter signals by confidence threshold"""

    def __init__(self, threshold: int = 50):
        self.threshold = threshold

    def adapt(self, data: Any, context: dict[str, Any]) -> Any:
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict) and d.get("confidence", 0) >= self.threshold]
        return data


# Adapter factory
def get_adapter(adapter_type: str) -> ContextAdapter:
    adapters = {
        "passthrough": PassthroughAdapter,
        "extract_signal": ExtractSignalAdapter,
        "merge_signals": MergeSignalsAdapter,
        "aggregate_confidence": AggregateConfidenceAdapter,
        "filter_by_confidence": FilterByConfidenceAdapter,
    }
    return adapters.get(adapter_type, PassthroughAdapter)()


# Message bus for inter-agent communication
class MessageBus:
    """Simple message bus for agent communication"""

    def __init__(self):
        self._messages: list[MessageFormat] = []

    def send(
        self,
        sender: str,
        recipient: str,
        intent: str,
        payload: dict[str, Any],
        metadata: dict | None = None,
    ):
        msg = MessageFormat(
            sender=sender,
            recipient=recipient,
            intent=intent,
            payload=payload,
            metadata=metadata or {},
        )
        self._messages.append(msg)

    def receive(self, recipient: str) -> list[MessageFormat]:
        return [m for m in self._messages if m.recipient == recipient]

    def broadcast(self, sender: str, intent: str, payload: dict[str, Any]):
        msg = MessageFormat(
            sender=sender,
            recipient="*",
            intent=intent,
            payload=payload,
        )
        self._messages.append(msg)

    def clear(self):
        self._messages.clear()

    def count(self) -> int:
        return len(self._messages)


# Singleton message bus
_BUS: MessageBus | None = None


def get_message_bus() -> MessageBus:
    global _BUS
    if _BUS is None:
        _BUS = MessageBus()
    return _BUS
