"""
HTTP connection handling for ai_urllib4.

This module provides classes for handling HTTP connections.
"""

from __future__ import annotations

import http.client
import logging
import socket
import ssl
import typing
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

log = logging.getLogger(__name__)

# Constants
RECENT_DATE = 2000  # For testing

# For backwards compatibility
CertificateError = ssl.SSLCertVerificationError

@dataclass
class ProxyConfig:
    """
    Configuration for a proxy connection.

    This class holds the configuration for a proxy connection.
    """

    proxy_url: Optional[str] = None
    proxy_headers: Optional[Dict[str, str]] = None
    proxy_ssl_context: Optional[ssl.SSLContext] = None
    use_forwarding_for_https: bool = False

    def __post_init__(self):
        """Initialize proxy headers if None."""
        if self.proxy_headers is None:
            self.proxy_headers = {}


class HTTPConnection(http.client.HTTPConnection):
    """
    HTTP connection that supports additional features.

    This class extends the standard library's HTTPConnection with
    additional features.
    """

    def __init__(
        self,
        host,
        port=None,
        timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
        source_address=None,
        blocksize=8192,
        **kwargs,
    ):
        """
        Initialize a new HTTPConnection.
        """
        super().__init__(
            host=host,
            port=port,
            timeout=timeout,
            source_address=source_address,
            blocksize=blocksize,
        )

    def connect(self):
        """Connect to the host and port specified in __init__."""
        return super().connect()


class HTTPSConnection(http.client.HTTPSConnection):
    """
    HTTPS connection that supports additional features.

    This class extends the standard library's HTTPSConnection with
    additional features.
    """

    def __init__(
        self,
        host,
        port=None,
        key_file=None,
        cert_file=None,
        timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
        source_address=None,
        context=None,
        blocksize=8192,
        **kwargs,
    ):
        """
        Initialize a new HTTPSConnection.
        """
        # Python 3.12+ deprecated/removed key_file and cert_file in favor of context.
        # We handle them here for backwards compatibility if needed.
        if (key_file or cert_file) and not context:
            context = ssl.create_default_context()
            if cert_file:
                context.load_cert_chain(cert_file, key_file)
        
        # Filter out arguments that http.client.HTTPSConnection might not support in newer Python versions
        init_kwargs = {
            "host": host,
            "port": port,
            "timeout": timeout,
            "source_address": source_address,
            "context": context,
            "blocksize": blocksize,
        }
        
        self.spki_pins = kwargs.pop("spki_pins", None)
        self.cert_transparency_policy = kwargs.pop("cert_transparency_policy", None)

        # Only pass check_hostname if it's explicitly provided and supported
        if "check_hostname" in kwargs:
            init_kwargs["check_hostname"] = kwargs.pop("check_hostname")

        super().__init__(**init_kwargs)

    def connect(self):
        """Connect to the host and port specified in __init__."""
        super().connect()
        
        if self.spki_pins or self.cert_transparency_policy:
            self._verify_security()

    def _verify_security(self):
        """Perform SPKI pinning and Certificate Transparency verification."""
        if not self.sock:
            return

        # Get the binary certificate
        binary_cert = self.sock.getpeercert(binary_form=True)
        if not binary_cert:
            log.warning("Could not get peer certificate for security verification")
            return

        from cryptography import x509
        cert = x509.load_der_x509_certificate(binary_cert)

        # 1. Verify SPKI Pinning
        if self.spki_pins:
            from .util.cert_verification import SPKIPinningVerifier
            verifier = SPKIPinningVerifier(self.spki_pins)
            if not verifier.verify_cert_for_host(cert, self.host):
                self.close()
                from .exceptions import SSLError
                raise SSLError(f"SPKI pinning verification failed for {self.host}")

        # 2. Verify Certificate Transparency
        if self.cert_transparency_policy:
            from .util.cert_verification import CertificateTransparencyVerifier
            verifier = CertificateTransparencyVerifier(policy=self.cert_transparency_policy)
            if not verifier.verify_cert(cert):
                self.close()
                from .exceptions import SSLError
                raise SSLError(f"Certificate Transparency verification failed for {self.host}")


class DummyConnection:
    """
    Dummy connection that does nothing.

    This class is used as a placeholder for connections that don't
    need to do anything.
    """

    def __init__(self):
        """Initialize a new DummyConnection."""
        pass

    def close(self):
        """Close the connection."""
        pass


# Exceptions for backwards compatibility
class HTTPException(Exception):
    """Base exception for HTTP errors."""
    pass


def _url_from_connection(conn: Union[HTTPConnection, HTTPSConnection]) -> str:
    """
    Get the URL from a connection.

    Args:
        conn: The connection to get the URL from.

    Returns:
        The URL.
    """
    scheme = "https" if isinstance(conn, HTTPSConnection) else "http"
    return f"{scheme}://{conn.host}:{conn.port}"


def _match_hostname(cert: Dict[str, Any], hostname: str) -> None:
    """
    Match a hostname to a certificate.

    Args:
        cert: The certificate to match.
        hostname: The hostname to match.

    Raises:
        CertificateError: If the hostname doesn't match the certificate.
    """
    try:
        ssl.match_hostname(cert, hostname)
    except ssl.CertificateError as e:
        raise CertificateError(str(e))


def _wrap_proxy_error(err: Exception) -> Exception:
    """
    Wrap a proxy error.

    Args:
        err: The error to wrap.

    Returns:
        The wrapped error.
    """
    from ai_urllib4.exceptions import ProxyError

    return ProxyError("Error connecting to proxy", err)
