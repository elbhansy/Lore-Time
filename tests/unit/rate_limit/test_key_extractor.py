"""Unit tests for Key Extractor and Trusted Proxy Defense."""

from starlette.requests import Request

from apps.api.app.core.rate_limit.key_extractor import (
    build_rate_limit_key,
    extract_client_identity,
)


def make_mock_request(client_host: str, xff: str | None = None) -> Request:
    scope = {
        "type": "http",
        "client": (client_host, 12345),
        "headers": [],
    }
    if xff:
        scope["headers"].append((b"x-forwarded-for", xff.encode("latin-1")))
    return Request(scope)


def test_untrusted_client_cannot_spoof_ip():
    """If client.host is untrusted, X-Forwarded-For is STRICTLY IGNORED."""
    trusted_proxies = ["127.0.0.1", "10.0.0.1"]

    # Malicious external client (203.0.113.50) sends spoofed XFF claiming to be 192.168.1.1
    req = make_mock_request(client_host="203.0.113.50", xff="192.168.1.1, 10.0.0.1")
    extracted_ip = extract_client_identity(req, trusted_proxies)

    # Must resolve to the direct untrusted peer, NOT the spoofed header
    assert extracted_ip == "203.0.113.50"


def test_trusted_proxy_extracts_client_ip():
    """If client.host IS a trusted proxy, leftmost X-Forwarded-For is extracted."""
    trusted_proxies = ["127.0.0.1", "10.0.0.1"]

    # Local reverse proxy (127.0.0.1) forwards request from real client 198.51.100.22
    req = make_mock_request(client_host="127.0.0.1", xff="198.51.100.22, 10.0.0.1")
    extracted_ip = extract_client_identity(req, trusted_proxies)

    assert extracted_ip == "198.51.100.22"


def test_build_rate_limit_key_deterministic():
    k1 = build_rate_limit_key(
        "EXPENSIVE_READ", "192.168.1.1", "/api/v1/series/1/world-state", "GET"
    )
    k2 = build_rate_limit_key(
        "EXPENSIVE_READ", "192.168.1.1", "/api/v1/series/2/world-state", "GET"
    )

    assert k1 == k2
    assert k1 == "rl:EXPENSIVE_READ:192.168.1.1"
