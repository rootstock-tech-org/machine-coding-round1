"""HMAC-signed URLs.                                         >>> TASK 1 <<<

Implement `sign_url` and `verify_url` using only the standard library.

Spec (the mock server and tests rely on it exactly):

* `path` is the URL path, e.g. "/files/vid-001".
* `expires` is an integer unix timestamp: int(now + ttl_seconds).
* String to sign (UTF-8):  f"GET\\n{path}\\n{expires}"
* Signature: lowercase hex HMAC-SHA256 of that string, keyed with `secret`.
* Signed URL: f"{base_url}{path}?expires={expires}&sig={signature}"

NOTE: the mock server imports this module to issue and check download URLs,
so the end-to-end run only works once this task is done.
"""

from enum import Enum


class Verdict(Enum):
    VALID = "valid"
    EXPIRED = "expired"  # signature is correct but the URL is past `expires`
    INVALID = "invalid"  # missing/malformed params or signature mismatch


def sign_url(
    base_url: str,
    path: str,
    secret: bytes,
    ttl_seconds: int,
    now: float | None = None,
) -> str:
    """Return a URL for `path` that is valid until int(now + ttl_seconds).

    `now` defaults to time.time(); tests pass it explicitly.
    """
    raise NotImplementedError


def verify_url(url: str, secret: bytes, now: float | None = None) -> Verdict:
    """Check a URL produced by `sign_url`.

    Returns INVALID if `expires`/`sig` are missing or malformed, or the
    signature does not match the URL's path and expiry; otherwise EXPIRED if
    now > expires; otherwise VALID.
    """
    raise NotImplementedError
