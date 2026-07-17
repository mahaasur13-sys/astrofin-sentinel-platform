"""web/utils/notifications.py — Centralized toast notifications (ATOM-META-RL-005)"""

from __future__ import annotations
import dash_bootstrap_components as dbc
from dash import html

TOAST_STYLES = {
    "position": "fixed",
    "top": 70,
    "right": 20,
    "width": 360,
    "zIndex": 9999,
    "boxShadow": "0 4px 12px rgba(0,0,0,0.4)",
}


def make_toast(
    message: str,
    title: str = "Notification",
    icon: str = "success",  # "success" | "danger" | "warning" | "info"
    duration: int = 4500,
    dismissable: bool = True,
) -> dbc.Toast:
    icon_map = {
        "success": "bi bi-check-circle-fill text-success",
        "danger": "bi bi-x-circle-fill text-danger",
        "warning": "bi bi-exclamation-triangle-fill text-warning",
        "info": "bi bi-info-circle-fill text-info",
    }
    icon_class = icon_map.get(icon, "bi bi-info-circle-fill text-info")
    return dbc.Toast(
        [
            html.Div(
                [
                    html.I(
                        className=icon_class,
                        style={"fontSize": "1.1rem", "marginRight": "8px"},
                    ),
                    html.Span(message, style={"fontSize": "0.875rem"}),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
        ],
        id={"type": "toast", "index": f"{title}_{id(message)}"},
        header=html.Div(
            [
                html.Strong(title, style={"fontSize": "0.9rem"}),
            ]
        ),
        icon=None,
        duration=duration,
        is_open=True,
        dismissable=dismissable,
        style=TOAST_STYLES,
        className="border-0",
        # dbc colors mapped to Bootstrap
        color=icon,  # works with dbc.Toast
    )


def make_toast_container(toasts: list) -> html.Div:
    """Wrap multiple toasts."""
    return html.Div(
        toasts,
        id="toast-container",
        style={"position": "fixed", "top": 70, "right": 20, "zIndex": 9999},
    )


# Singleton store for active toasts
_toast_counter = 0


def next_toast_id(prefix="Toast"):
    global _toast_counter
    _toast_counter += 1
    return f"{prefix}_{_toast_counter}"
