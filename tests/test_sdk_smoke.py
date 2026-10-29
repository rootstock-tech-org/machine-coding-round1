"""Shows how the mock LLM SDK behaves. Delete or keep -- your own tests go next to it."""

import pytest

from llm_sdk import ContextLengthExceeded, LLMClient, count_tokens


async def test_extracts_fields_as_json_like_text():
    client = LLMClient("key", server_error_rate=0, malformed_rate=0, latency=(0, 0))
    completion = await client.complete("Vendor: Acme\nInvoice No: INV-12345\nGrand Total: INR 1,000.00")
    assert '"invoice_number": "INV-12345"' in completion.text
    assert completion.cost_usd > 0


async def test_context_window_is_enforced():
    client = LLMClient("key", latency=(0, 0))
    with pytest.raises(ContextLengthExceeded):
        await client.complete("x" * 10_000)
    assert count_tokens("x" * 10_000) == 2500
