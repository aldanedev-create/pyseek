from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


def canonicalize(url: str) -> str:
    parts = urlsplit((url or "").strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Only public http(s) URLs are accepted")
    host = parts.hostname.lower().rstrip(".")
    if host == "localhost" or _is_private_host(host):
        raise ValueError("Private or local addresses are not crawlable")
    port = parts.port
    if port and ((parts.scheme == "http" and port != 80) or (parts.scheme == "https" and port != 443)):
        netloc = f"{host}:{port}"
    else:
        netloc = host
    path = parts.path or "/"
    return urlunsplit((parts.scheme, netloc, path, parts.query, ""))


def _is_private_host(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            return any(ipaddress.ip_address(item[4][0]).is_private or ipaddress.ip_address(item[4][0]).is_loopback for item in infos)
        except (OSError, ValueError):
            return False
