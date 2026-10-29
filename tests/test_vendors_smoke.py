"""Shows how the vendor SDKs behave. Delete or keep -- your own tests go next to it."""

from vendors.alpha import AlphaClient
from vendors.beta import BetaMarketsClient


def test_alpha_returns_paise_ints():
    quotes = AlphaClient("key", failure_rate=0, seed=1).get_quotes(["TCS", "UNKNOWN"])
    assert [q["sym"] for q in quotes] == ["TCS"]
    assert isinstance(quotes[0]["ltp_paise"], int)


def test_beta_returns_decimal_strings():
    tick = BetaMarketsClient("token", failure_rate=0, stale_rate=0, seed=1).fetch("NSE:TCS")
    assert tick.instrument == "NSE:TCS"
    assert isinstance(tick.last_price, str) and "." in tick.last_price
