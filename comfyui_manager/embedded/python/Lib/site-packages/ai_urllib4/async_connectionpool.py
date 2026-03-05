"""
Async Connection pool implementation for ai_urllib4.

This module provides async classes for managing pools of connections.
"""

from __future__ import annotations

import asyncio
import logging
import typing
from urllib.parse import urlparse

# We'll use the sync exceptions for now, or define new async ones if needed
from .exceptions import ClosedPoolError, EmptyPoolError, PoolError

log = logging.getLogger(__name__)


class AsyncConnectionPool:
    """
    Base class for async connection pools.
    """
    
    def __init__(self, host: str, port: int | None = None):
        self.host = host
        self.port = port
        
    async def close(self) -> None:
        """Close all connections in the pool."""
        pass

    async def __aenter__(self) -> "AsyncConnectionPool":
        return self

    async def __aexit__(self, exc_type: typing.Any, exc_val: typing.Any, exc_tb: typing.Any) -> None:
        await self.close()


class AsyncHTTPConnectionPool(AsyncConnectionPool):
    """
    Async connection pool for HTTP connections.
    """
    
    scheme = "http"
    
    def __init__(
        self,
        host: str,
        port: int | None = None,
        timeout: float | None = None,
        maxsize: int = 1,
        block: bool = False,
        **conn_kw: typing.Any,
    ):
        super().__init__(host, port)
        self.timeout = timeout
        self.maxsize = maxsize
        self.block = block
        self.conn_kw = conn_kw
        self.pool: asyncio.Queue[typing.Any] = asyncio.Queue(maxsize=maxsize)
        self.num_connections = 0
        self.closed = False
        
    async def _get_conn(self) -> typing.Any:
        """Get a connection from the pool."""
        if self.closed:
            raise ClosedPoolError(self, "Pool is closed")
            
        try:
            # Try to get a connection from the queue without blocking first
            return self.pool.get_nowait()
        except asyncio.QueueEmpty:
            if self.num_connections < self.maxsize:
                # Create a new connection place holder (mocking actual connection creation for this stub)
                self.num_connections += 1
                return self._new_conn()
            
            if not self.block:
                raise EmptyPoolError(self, "Pool is empty and blocking is disabled")
                
            # Wait for a connection
            return await self.pool.get()

    def _new_conn(self) -> typing.Any:
        # Placeholder for actual async connection creation
        return object()

    async def _put_conn(self, conn: typing.Any) -> None:
        """Put a connection back into the pool."""
        if self.closed:
            return
            
        await self.pool.put(conn)

    async def urlopen(
        self,
        method: str,
        url: str,
        body: typing.Any = None,
        headers: dict[str, str] | None = None,
        **response_kw: typing.Any,
    ) -> str:
        """
        Make an async request using asyncio streams.
        """
        conn = await self._get_conn()
        reader = None
        writer = None
        try:
            # 1. Parse URL (rudimentary for this demo)
            # Assuming url is just path if host is in pool, or full url
            path = url
            if url.startswith("http"):
                parsed = urlparse(url)
                path = parsed.path or "/"

            # 2. Open Connection
            # In a real pool, we'd reuse 'conn' if it was an open socket
            # For this v1, we open a new connection every time
            reader, writer = await asyncio.open_connection(self.host, self.port or 80)

            # 3. Construct Request
            request_lines = [
                f"{method} {path} HTTP/1.1",
                f"Host: {self.host}",
                "Connection: close", # Simple one-off
                "User-Agent: ai_urllib4/2.0.0"
            ]
            if headers:
                for k, v in headers.items():
                    request_lines.append(f"{k}: {v}")
            
            request_lines.append("\r\n")
            request_data = "\r\n".join(request_lines).encode("ascii")

            # 4. Send Request
            writer.write(request_data)
            await writer.drain()

            # 5. Read Response (Basic)
            response_data = b""
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # 6. Decode (Simulated Response Object)
            return response_data.decode("utf-8", errors="replace")

        except Exception as e:
            return f"Error: {e}"
        finally:
            if writer:
                writer.close()
                await writer.wait_closed()
            await self._put_conn(conn)

    async def close(self) -> None:
        self.closed = True
        # Drain queue?
        pass


def connection_from_url(url: str, **kw: typing.Any) -> AsyncConnectionPool:
    parsed = urlparse(url)
    scheme = parsed.scheme
    host = parsed.netloc
    port = parsed.port
    
    if scheme == "http":
        return AsyncHTTPConnectionPool(host, port, **kw)
    elif scheme == "https":
        # For now return HTTP pool as placeholder or implement HTTPS
        return AsyncHTTPConnectionPool(host, port, **kw)
    else:
        raise ValueError(f"Unsupported scheme: {scheme}")
