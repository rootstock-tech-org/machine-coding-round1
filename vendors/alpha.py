"""AlphaQuotes SDK -- mock of a third-party market data vendor. DO NOT MODIFY.

Quirks you must deal with:
* Prices are integer **paise** (1 rupee = 100 paise).
* Symbols are plain: "RELIANCE", "TCS".
* Timestamps are unix epoch seconds (int, UTC).
* At most 3 symbols per request.
* Unknown symbols are silently omitted from the response.
* Fails randomly with AlphaError(429) or AlphaError(503).
"""

import random
import time

_BASE_PAISE = {
    "RELIANCE": 295_000,
    "TCS": 410_000,
    "INFY": 185_000,
    "HDFCBANK": 165_000,
    "SBIN": 82_000,
    "ITC": 46_000,
}


class AlphaError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code


class AlphaClient:
    MAX_SYMBOLS_PER_REQUEST = 3

    def __init__(self, api_key: str, *, failure_rate: float = 0.1, seed: int | None = None) -> None:
        if not api_key:
            raise AlphaError(401, "missing api key")
        self._rng = random.Random(seed)
        self._failure_rate = failure_rate
        self._prices = dict(_BASE_PAISE)

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """Return e.g. [{"sym": "TCS", "ltp_paise": 410250, "ts": 1730000000}]."""
        if len(symbols) > self.MAX_SYMBOLS_PER_REQUEST:
            raise AlphaError(400, f"max {self.MAX_SYMBOLS_PER_REQUEST} symbols per request")
        roll = self._rng.random()
        if roll < self._failure_rate / 2:
            raise AlphaError(503, "service unavailable")
        if roll < self._failure_rate:
            raise AlphaError(429, "rate limited")
        time.sleep(self._rng.uniform(0.005, 0.03))

        quotes = []
        for sym in symbols:
            if sym not in self._prices:
                continue
            self._prices[sym] = max(100, int(self._prices[sym] * self._rng.uniform(0.99, 1.01)))
            quotes.append({"sym": sym, "ltp_paise": self._prices[sym], "ts": int(time.time())})
        return quotes
