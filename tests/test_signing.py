from urllib.parse import parse_qs, urlparse

from ingestion.signing import Verdict, sign_url, verify_url

SECRET = b"test-secret"
BASE = "https://cdn.example.com"
NOW = 1_700_000_000.0


def _signed(path="/files/a", ttl=60):
    return sign_url(BASE, path, SECRET, ttl, now=NOW)


def test_round_trip():
    url = _signed()
    assert url.startswith(BASE + "/files/a?")
    assert verify_url(url, SECRET, now=NOW + 30) is Verdict.VALID


def test_expires_is_now_plus_ttl():
    query = parse_qs(urlparse(_signed(ttl=60)).query)
    assert int(query["expires"][0]) == int(NOW + 60)


def test_expired():
    assert verify_url(_signed(ttl=60), SECRET, now=NOW + 61) is Verdict.EXPIRED


def test_wrong_secret():
    assert verify_url(_signed(), b"other-secret", now=NOW) is Verdict.INVALID


def test_tampered_path():
    url = _signed().replace("/files/a", "/files/b")
    assert verify_url(url, SECRET, now=NOW) is Verdict.INVALID


def test_tampered_expiry():
    url = _signed(ttl=60).replace(f"expires={int(NOW + 60)}", f"expires={int(NOW + 6000)}")
    assert verify_url(url, SECRET, now=NOW) is Verdict.INVALID


def test_missing_params():
    assert verify_url(BASE + "/files/a", SECRET, now=NOW) is Verdict.INVALID
