#!/usr/bin/env python3
"""Payload formatting for the alert relay: Alertmanager v4 object and legacy list."""

import importlib.util
from pathlib import Path

RELAY = Path(__file__).resolve().parents[1] / "artifacts" / "alert-relay" / "alert_relay.py"

_spec = importlib.util.spec_from_file_location("alert_relay", RELAY)
relay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(relay)

AM_V4 = {
    "version": "4",
    "status": "firing",
    "receiver": "relay",
    "groupKey": '{}:{alertname="WALGBackupFailed"}',
    "commonLabels": {"alertname": "WALGBackupFailed", "severity": "warning"},
    "commonAnnotations": {"summary": "WAL-G backup failed"},
    "externalURL": "http://127.0.0.1:9093",
    "alerts": [
        {
            "status": "firing",
            "labels": {"alertname": "WALGBackupFailed", "severity": "warning"},
            "annotations": {"summary": "WAL-G backup failed"},
            "startsAt": "2026-10-22T03:57:00Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "fingerprint": "abc123",
        }
    ],
}


def test_alertmanager_v4_title_from_common_labels():
    text = relay.format_payload(AM_V4)
    assert text.splitlines()[0] == "[FIRING] WALGBackupFailed"
    assert "- firing: WALGBackupFailed | WAL-G backup failed" in text
    assert "http://127.0.0.1:9093" in text


def test_legacy_list_payload_is_accepted():
    legacy = [
        {
            "status": "firing",
            "labels": {"alertname": "ZoDeliveryProbe"},
            "annotations": {"summary": "probe"},
        }
    ]
    text = relay.format_payload(legacy)
    assert text.splitlines()[0] == "[?] Grafana alert"
    assert "- firing: ZoDeliveryProbe | probe" in text


def test_unknown_shape_does_not_raise():
    assert relay.format_payload("nonsense").splitlines()[0] == "[?] Grafana alert"


def test_resolved_status_is_rendered():
    text = relay.format_payload({"status": "resolved", "alerts": []})
    assert text.splitlines()[0] == "[RESOLVED] Grafana alert"
