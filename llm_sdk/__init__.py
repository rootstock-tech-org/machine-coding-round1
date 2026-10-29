"""Mock LLM provider SDK. DO NOT MODIFY.

Behaves like a hosted LLM API, scaled down so it runs locally:

* `await client.complete(prompt, max_output_tokens=...)` returns a Completion.
* Context window: input tokens + max_output_tokens must be <= MAX_CONTEXT_TOKENS,
  otherwise ContextLengthExceeded.
* Rate limits per client: `rpm` requests and `tpm` tokens (input + max output)
  per rolling 60 seconds, and at most `max_concurrent` requests in flight.
  Exceeding any of them raises RateLimitError with a `retry_after` hint.
* Random ServerError (HTTP 500-like) failures.
* The model is an invoice field extractor. It replies with JSON for the fields
  invoice_number, vendor, invoice_date, currency, total -- using null for
  anything it cannot see in the prompt. Like a real model it is imperfect:
  it sometimes wraps or breaks the JSON, its output is cut off at
  max_output_tokens, and it only normalises values when the prompt explicitly
  asks for a format (e.g. "YYYY-MM-DD").
* Usage is billed: see Completion.cost_usd.
"""

import asyncio
import json
import random
import re
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime

MODEL = "mock-extract-1"
MAX_CONTEXT_TOKENS = 2048
USD_PER_1K_INPUT = 0.0005
USD_PER_1K_OUTPUT = 0.0015


def count_tokens(text: str) -> int:
    """The provider's tokenizer. Use it for budgeting -- it's exact for this model."""
    return max(1, len(text) // 4)


class LLMError(Exception):
    pass


class RateLimitError(LLMError):
    def __init__(self, message: str, retry_after: float) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(LLMError):
    pass


class ContextLengthExceeded(LLMError):
    pass


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model: str = MODEL


_PATTERNS = {
    "invoice_number": r"Invoice\s*(?:No\.?|Number|#)\s*[:\-]?\s*([A-Z]{2,4}-\d{4,8})",
    "vendor": r"(?:Vendor|Supplier|From)\s*:\s*([^\n]+)",
    "invoice_date": r"(?:Invoice Date|Date of Issue|Dated)\s*:\s*([^\n]+)",
    "currency": r"Currency\s*:\s*([A-Z]{3})",
    "total": r"(?:Grand Total|Total Due|Amount Payable)\s*:\s*[A-Z]{0,3}\s*([\d,]+\.\d{2})",
}
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%d %b %Y")


class LLMClient:
    def __init__(
        self,
        api_key: str,
        *,
        rpm: int = 300,
        tpm: int = 200_000,
        max_concurrent: int = 8,
        server_error_rate: float = 0.05,
        malformed_rate: float = 0.08,
        latency: tuple[float, float] = (0.05, 0.4),
        seed: int | None = None,
    ) -> None:
        if not api_key:
            raise LLMError("missing api key")
        self.rpm, self.tpm, self.max_concurrent = rpm, tpm, max_concurrent
        self._server_error_rate = server_error_rate
        self._malformed_rate = malformed_rate
        self._latency = latency
        self._rng = random.Random(seed)
        self._window: deque[tuple[float, int]] = deque()
        self._in_flight = 0
        self.total_requests = 0

    async def complete(self, prompt: str, *, max_output_tokens: int = 256) -> Completion:
        input_tokens = count_tokens(prompt)
        if input_tokens + max_output_tokens > MAX_CONTEXT_TOKENS:
            raise ContextLengthExceeded(
                f"{input_tokens} input + {max_output_tokens} output > {MAX_CONTEXT_TOKENS}"
            )
        self._admit(input_tokens + max_output_tokens)
        self._in_flight += 1
        self.total_requests += 1
        try:
            await asyncio.sleep(self._rng.uniform(*self._latency))
            if self._rng.random() < self._server_error_rate:
                raise ServerError("500 internal server error")
            text = self._respond(prompt)
            if count_tokens(text) > max_output_tokens:
                text = text[: max_output_tokens * 4]
            output_tokens = count_tokens(text)
            cost = input_tokens / 1000 * USD_PER_1K_INPUT + output_tokens / 1000 * USD_PER_1K_OUTPUT
            return Completion(text, input_tokens, output_tokens, round(cost, 8))
        finally:
            self._in_flight -= 1

    def _admit(self, tokens: int) -> None:
        now = time.monotonic()
        while self._window and now - self._window[0][0] >= 60:
            self._window.popleft()
        if self._in_flight >= self.max_concurrent:
            raise RateLimitError("too many concurrent requests", retry_after=0.5)
        used = sum(t for _, t in self._window)
        if len(self._window) >= self.rpm or used + tokens > self.tpm:
            retry_after = 60 - (now - self._window[0][0]) if self._window else 1.0
            raise RateLimitError("rate limit exceeded", retry_after=round(max(retry_after, 0.1), 2))
        self._window.append((now, tokens))

    def _respond(self, prompt: str) -> str:
        fields: dict[str, str | None] = {}
        for name, pattern in _PATTERNS.items():
            matches = re.findall(pattern, prompt)
            # totals appear at the end of an invoice; everything else at the top
            fields[name] = (matches[-1] if name == "total" else matches[0]).strip() if matches else None
        if "YYYY-MM-DD" in prompt and fields["invoice_date"]:
            fields["invoice_date"] = _normalise_date(fields["invoice_date"])
        text = json.dumps(fields)

        roll = self._rng.random()
        if roll < self._malformed_rate * 0.4:
            return f"```json\n{text}\n```"
        if roll < self._malformed_rate * 0.7:
            return f"Sure! Here are the extracted fields:\n{text}"
        if roll < self._malformed_rate:
            return text[: len(text) * 2 // 3]
        return text


def _normalise_date(raw: str) -> str:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw
