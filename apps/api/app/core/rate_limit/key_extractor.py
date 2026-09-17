"""Client Key Extractor with Trusted Proxy Protection."""

from starlette.requests import Request


def extract_client_identity(request: Request, trusted_proxies: list[str]) -> str:
    """Extracts client IP identity securely.

    Hard Rule / Security Guarantee:
    - If the direct socket peer (client.host) is NOT in trusted_proxies,
      X-Forwarded-For is STRICTLY IGNORED to prevent client IP spoofing and victim framing.
    - If and only if the direct socket peer IS in trusted_proxies, the leftmost
      IP from X-Forwarded-For is extracted.
    """
    direct_peer = request.client.host if request.client else "unknown"

    if direct_peer not in trusted_proxies:
        return direct_peer

    # Peer is a verified trusted reverse proxy (e.g. localhost, local Nginx)
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # Leftmost IP represents the original client
        client_ip = xff.split(",")[0].strip()
        if client_ip:
            return client_ip

    return direct_peer


def build_rate_limit_key(tier: str, client_ip: str, path: str, method: str) -> str:
    """Generates a deterministic, bounded rate-limit key."""
    # Bucket paths by tier to prevent attacker route rotation while respecting tier boundaries
    return f"rl:{tier}:{client_ip}"
