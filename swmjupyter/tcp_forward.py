"""Localhost TCP forward for hub↔singleuser when internal SSL uses localhost SANs."""

from __future__ import annotations

import logging
import selectors
import socket
import threading
from typing import Optional

log = logging.getLogger(__name__)


class LocalTcpForward:
    """Forward ``127.0.0.1:local_port`` to ``remote_host:remote_port`` (TLS passthrough)."""

    def __init__(self, remote_host: str, remote_port: int) -> None:
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._listen: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.local_port = 0

    def start(self) -> int:
        if self._listen is not None:
            return self.local_port
        listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen.bind(("127.0.0.1", 0))
        listen.listen(128)
        listen.settimeout(1.0)
        self._listen = listen
        self.local_port = int(listen.getsockname()[1])
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._serve,
            name=f"swm-tcp-forward-{self.local_port}",
            daemon=True,
        )
        self._thread.start()
        log.info(
            "TCP forward 127.0.0.1:%s -> %s:%s",
            self.local_port,
            self._remote_host,
            self._remote_port,
        )
        return self.local_port

    def stop(self) -> None:
        self._stop.set()
        listen = self._listen
        self._listen = None
        if listen is not None:
            try:
                listen.close()
            except OSError:
                pass
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        self.local_port = 0

    def _serve(self) -> None:
        assert self._listen is not None
        while not self._stop.is_set():
            try:
                client, _addr = self._listen.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            thread = threading.Thread(
                target=self._relay_pair,
                args=(client,),
                daemon=True,
            )
            thread.start()

    def _relay_pair(self, client: socket.socket) -> None:
        remote: Optional[socket.socket] = None
        try:
            remote = socket.create_connection((self._remote_host, self._remote_port), timeout=30.0)
            client.settimeout(None)
            remote.settimeout(None)
            _bidirectional_relay(client, remote, self._stop)
        except OSError as exc:
            log.debug("TCP forward relay ended: %s", exc)
        finally:
            try:
                client.close()
            except OSError:
                pass
            if remote is not None:
                try:
                    remote.close()
                except OSError:
                    pass


def _bidirectional_relay(a: socket.socket, b: socket.socket, stop: threading.Event) -> None:
    sel = selectors.DefaultSelector()
    sel.register(a, selectors.EVENT_READ, b)
    sel.register(b, selectors.EVENT_READ, a)
    try:
        while not stop.is_set():
            events = sel.select(timeout=1.0)
            if not events:
                continue
            for key, _mask in events:
                src: socket.socket = key.fileobj  # type: ignore[assignment]
                dst: socket.socket = key.data
                try:
                    data = src.recv(65536)
                except OSError:
                    return
                if not data:
                    return
                try:
                    dst.sendall(data)
                except OSError:
                    return
    finally:
        sel.close()
