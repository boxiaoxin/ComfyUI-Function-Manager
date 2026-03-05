"""
HTTP/2 support for ai_urllib4.

This module provides HTTP/2 support for ai_urllib4, including enhanced features
like server push, adaptive flow control, and connection profiles.
"""

from __future__ import annotations

__all__ = [
    "inject_into_ai_urllib4",
    "extract_from_ai_urllib4",
    "ConnectionProfile",
    "FlowControlStrategy",
    "HTTP2Settings",
    "HTTP2Connection",
    "PushManager",
]

import typing

from .connection import HTTP2Connection
from .flow_control import FlowControlStrategy
from .push_manager import PushManager
from .settings import ConnectionProfile, HTTP2Settings, SettingsManager

orig_HTTPSConnection: typing.Any = None


def inject_into_ai_urllib4() -> None:
    """
    Inject HTTP/2 support into ai_urllib4.

    This function replaces the standard HTTPSConnection with the HTTP/2-capable
    HTTP2Connection, enabling HTTP/2 support for all HTTPS requests made through
    ai_urllib4.
    """
    import ai_urllib4.connection

    global orig_HTTPSConnection

    if orig_HTTPSConnection is not None:
        return

    orig_HTTPSConnection = ai_urllib4.connection.HTTPSConnection

    from .connection import HTTP2Connection

    ai_urllib4.connection.HTTPSConnection = HTTP2Connection


def extract_from_ai_urllib4() -> None:
    """
    Extract HTTP/2 support from ai_urllib4.

    This function restores the standard HTTPSConnection, disabling HTTP/2 support
    for HTTPS requests made through ai_urllib4.
    """
    import ai_urllib4.connection

    global orig_HTTPSConnection

    if orig_HTTPSConnection is None:
        return

    ai_urllib4.connection.HTTPSConnection = orig_HTTPSConnection
    orig_HTTPSConnection = None
