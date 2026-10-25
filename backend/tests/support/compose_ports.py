"""Test-only helper: finds Compose port bindings that are not pinned to 127.0.0.1."""

import os
import re
from typing import Any

_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
_PERMITTED_HOST_IP = "127.0.0.1"


def interpolate(value: str, env: dict[str, str] | None = None) -> str:
    """Expand `${VAR}` and `${VAR:-default}` the way Compose does for port strings."""
    source = os.environ if env is None else env

    def replace(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        if name in source and source[name] != "":
            return source[name]
        return default if default is not None else ""

    return _VAR.sub(replace, value)


def _short_violation(entry: str) -> str | None:
    """Return a violation message for a short-syntax port string, or None when it is safe."""
    text = interpolate(entry).split("/", 1)[0]
    if text.startswith("["):
        host_ip, _, rest = text[1:].partition("]")
        parts = rest.lstrip(":").split(":") if rest else []
        if not parts or len(parts) > 2:
            return f"{entry!r}: missing host IP"
        return (
            None
            if host_ip == _PERMITTED_HOST_IP
            else f"{entry!r}: host IP {host_ip!r} is not {_PERMITTED_HOST_IP}"
        )
    parts = text.split(":")
    if len(parts) == 2:
        return f"{entry!r}: missing host IP (binds to 0.0.0.0)"
    if len(parts) == 3:
        host_ip = parts[0]
        if host_ip == _PERMITTED_HOST_IP:
            return None
        if host_ip == "":
            return f"{entry!r}: missing host IP (binds to 0.0.0.0)"
        return f"{entry!r}: host IP {host_ip!r} is not {_PERMITTED_HOST_IP}"
    return f"{entry!r}: cannot parse port binding"


def _long_violation(entry: dict[str, Any]) -> str | None:
    host_ip = entry.get("host_ip")
    if host_ip is None or str(host_ip) == "":
        return f"{entry!r}: missing host IP (binds to 0.0.0.0)"
    if str(host_ip) != _PERMITTED_HOST_IP:
        return f"{entry!r}: host IP {host_ip!r} is not {_PERMITTED_HOST_IP}"
    return None


def find_non_loopback_ports(compose: dict[str, Any]) -> list[str]:
    """Return one message per published port that is not explicitly bound to 127.0.0.1."""
    violations: list[str] = []
    services: dict[str, Any] = compose.get("services") or {}
    for name, service in services.items():
        for entry in (service or {}).get("ports") or []:
            if isinstance(entry, str):
                message = _short_violation(entry)
            elif isinstance(entry, dict):
                message = _long_violation(entry)
            else:
                message = f"{entry!r}: unsupported port entry"
            if message is not None:
                violations.append(f"{name}: {message}")
    return violations
