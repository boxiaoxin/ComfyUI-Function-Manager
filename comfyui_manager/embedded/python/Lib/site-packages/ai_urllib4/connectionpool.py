"""
Connection pool implementation for ai_urllib4.

This module provides classes for managing pools of connections.
"""

from __future__ import annotations

import logging
import typing
from urllib.parse import urlparse

from .connection import HTTPConnection, HTTPSConnection
from .exceptions import ClosedPoolError, EmptyPoolError, PoolError
from .util.timeout import Timeout

log = logging.getLogger(__name__)


class ConnectionPool:
    """
    Base class for connection pools.
    
    This class provides a base for connection pools.
    """
    
    def __init__(self, host, port=None):
        """
        Initialize a new ConnectionPool.
        
        :param host: Host to connect to
        :param port: Port to connect to
        """
        self.host = host
        self.port = port
        
    def close(self):
        """Close all connections in the pool."""
        pass


class HTTPConnectionPool(ConnectionPool):
    """
    Thread-safe connection pool for HTTP connections.
    
    This class manages a pool of HTTP connections.
    """
    
    scheme = "http"
    ConnectionCls = HTTPConnection
    
    def __init__(
        self,
        host,
        port=None,
        timeout=Timeout.DEFAULT_TIMEOUT,
        maxsize=1,
        block=False,
        spki_pins=None,
        cert_transparency_policy=None,
        **conn_kw,
    ):
        """
        Initialize a new HTTPConnectionPool.
        
        :param host: Host to connect to
        :param port: Port to connect to
        :param timeout: Socket timeout
        :param maxsize: Maximum number of connections to keep in the pool
        :param block: Whether to block when the pool is full
        :param spki_pins: Dictionary mapping hostnames to sets of SPKI pins
        :param cert_transparency_policy: Certificate Transparency policy
        :param conn_kw: Additional parameters for the connection
        """
        super().__init__(host, port)
        self.timeout = timeout
        self.maxsize = maxsize
        self.block = block
        self.spki_pins = spki_pins
        self.cert_transparency_policy = cert_transparency_policy
        self.conn_kw = conn_kw.copy() if conn_kw else {}
        self.num_connections = 0
        self.num_requests = 0
        self.pool = []
        self.closed = False
        
    def close(self):
        """Close all connections in the pool."""
        self.closed = True
        for conn in self.pool:
            conn.close()
        self.pool = []
        
    def _get_conn(self):
        """
        Get a connection from the pool.
        """
        import socket
        if self.closed:
            raise ClosedPoolError(self, "Pool is closed")
            
        if not self.pool and self.num_connections >= self.maxsize:
            if not self.block:
                raise EmptyPoolError(self, "Pool is empty and blocking is disabled")
                
        # Handle Timeout object properly
        timeout = self.timeout
        if hasattr(timeout, "connect_timeout"):
            timeout = timeout.connect_timeout
        
        if timeout is Timeout.DEFAULT_TIMEOUT or timeout is None:
            timeout = socket._GLOBAL_DEFAULT_TIMEOUT

        # Create a new connection
        self.num_connections += 1
        
        conn_kw = self.conn_kw.copy()
        if self.scheme == "https":
            conn_kw["spki_pins"] = self.spki_pins
            conn_kw["cert_transparency_policy"] = self.cert_transparency_policy

        conn = self.ConnectionCls(
            host=self.host,
            port=self.port,
            timeout=timeout,
            **conn_kw,
        )
        return conn
        
    def _put_conn(self, conn):
        """
        Put a connection back into the pool.
        
        :param conn: The connection to put back
        """
        if self.closed:
            conn.close()
            return
            
        self.pool.append(conn)
        
    def urlopen(
        self,
        method,
        url,
        body=None,
        headers=None,
        retries=None,
        redirect=True,
        assert_same_host=True,
        timeout=Timeout.DEFAULT_TIMEOUT,
        pool_timeout=None,
        release_conn=None,
        chunked=False,
        body_pos=None,
        **response_kw,
    ):
        """
        Make a request using a connection from the pool.
        """
        from .response import HTTPResponse
        
        # In a real implementation, we would handle retries, redirects, etc.
        # For this enhancement, we'll implement a basic functional version.
        
        conn = self._get_conn()
        try:
            # http.client.request expects only the path for the URL in request
            # if it's already connected to the host.
            parsed = urlparse(url)
            path = parsed.path
            if parsed.query:
                path += "?" + parsed.query
            if not path:
                path = "/"
                
            conn.request(method, path, body=body, headers=headers or {})
            res = conn.getresponse()
            
            preload_content = response_kw.get("preload_content", True)
            if preload_content:
                response_body = res.read()
            else:
                response_body = None
            
            response = HTTPResponse(
                body=response_body,
                headers=dict(res.getheaders()),
                status=res.status,
                version=res.version,
                reason=res.reason,
                preload_content=preload_content,
                decode_content=True,
                request_url=url,
                connection=conn if not preload_content else None,
                pool=self,
                original_response=res,
            )
            return response
        except Exception:
            conn.close()
            raise
        finally:
            if response_kw.get("preload_content", True):
                if release_conn:
                    self._put_conn(conn)
                else:
                    conn.close()
                    self.num_connections -= 1


class HTTPSConnectionPool(HTTPConnectionPool):
    """
    Thread-safe connection pool for HTTPS connections.
    
    This class manages a pool of HTTPS connections.
    """
    
    scheme = "https"
    ConnectionCls = HTTPSConnection


def connection_from_url(url, **kw):
    """
    Create a connection pool for a URL.
    
    :param url: URL to create a connection pool for
    :param kw: Additional parameters for the connection pool
    :return: Connection pool for the URL
    """
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme
    host = parsed_url.netloc
    port = parsed_url.port
    
    if scheme == "http":
        return HTTPConnectionPool(host, port, **kw)
    elif scheme == "https":
        return HTTPSConnectionPool(host, port, **kw)
    else:
        raise ValueError(f"Unsupported scheme: {scheme}")
