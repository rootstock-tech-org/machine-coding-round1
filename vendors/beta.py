"""BetaMarkets SDK -- mock of a second market data vendor. DO NOT MODIFY.

Quirks you must deal with (all different from Alpha, on purpose):
* Instruments are exchange-prefixed: "NSE:RELIANCE".
* Prices are **decimal strings in rupees**: "2950.25".
* Timestamps are ISO-8601 strings with an offset: "2026-10-30T09:15:02+05:30".
* One instrument per request.
* Unknown instruments raise BetaUnknownInstrument.
* Sometimes returns a **stale** tick (as_of several minutes old) without any error.
* Fails randomly with BetaTimeout.
"""

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

_BASE_RUPEES = {
    "NSE:RELIANCE": 2951.10,
    "NSE:TCS": 4098.40,
    "NSE:INFY": 1849.75,
    "NSE:HDFCBANK": 1651.20,
    "NSE:SBIN": 819.65,
    "NSE:WIPRO": 562.30,
}


class BetaError(Exception):
    pass


class BetaTimeout(BetaError):
    pass


class BetaUnknownInstrument(BetaError):
    pass


@dataclass(frozen=True)
class BetaTick:
    instrument: str
    last_price: str
    as_of: str


class BetaMarketsClient:
    def __init__(self, token: str, *, failure_rate: float = 0.1, stale_rate: float = 0.1,
                 seed: int | None = None) -> None:
        if not token:
            raise BetaError("missing token")
        self._rng = random.Random(seed)
        self._failure_rate = failure_rate
        self._stale_rate = stale_rate
        self._prices = dict(_BASE_RUPEES)

    def fetch(self, instrument: str) -> BetaTick:
        if self._rng.random() < self._failure_rate:
            raise BetaTimeout(f"timed out fetching {instrument}")
        if instrument not in self._prices:
            raise BetaUnknownInstrument(instrument)
        time.sleep(self._rng.uniform(0.005, 0.03))

        self._prices[instrument] = round(self._prices[instrument] * self._rng.uniform(0.99, 1.01), 2)
        as_of = datetime.now(IST)
        if self._rng.random() < self._stale_rate:
            as_of -= timedelta(minutes=self._rng.randint(3, 15))
        return BetaTick(
            instrument=instrument,
            last_price=f"{self._prices[instrument]:.2f}",
            as_of=as_of.isoformat(timespec="seconds"),
        )
