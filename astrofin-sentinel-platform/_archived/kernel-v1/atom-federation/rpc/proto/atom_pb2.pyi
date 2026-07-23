from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class AtomMessage(_message.Message):
    __slots__ = ("meta", "msg_id", "payload", "source", "target", "timestamp", "ttl")
    class MetaEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: str | None = ..., value: str | None = ...) -> None: ...
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    msg_id: str
    source: str
    target: str
    payload: str
    timestamp: int
    ttl: int
    meta: _containers.ScalarMap[str, str]
    def __init__(self, msg_id: str | None = ..., source: str | None = ..., target: str | None = ..., payload: str | None = ..., timestamp: int | None = ..., ttl: int | None = ..., meta: _Mapping[str, str] | None = ...) -> None: ...

class Ack(_message.Message):
    __slots__ = ("error", "msg_id", "ok", "seq")
    OK_FIELD_NUMBER: _ClassVar[int]
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    msg_id: str
    error: str
    seq: int
    def __init__(self, ok: bool = ..., msg_id: str | None = ..., error: str | None = ..., seq: int | None = ...) -> None: ...

class AtomAck(_message.Message):
    __slots__ = ("error", "msg_id", "ok", "server_ts")
    MSG_ID_FIELD_NUMBER: _ClassVar[int]
    OK_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    SERVER_TS_FIELD_NUMBER: _ClassVar[int]
    msg_id: str
    ok: bool
    error: str
    server_ts: int
    def __init__(self, msg_id: str | None = ..., ok: bool = ..., error: str | None = ..., server_ts: int | None = ...) -> None: ...
