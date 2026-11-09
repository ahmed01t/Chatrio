"""
Unit tests for the Sliding Window Debounce Buffer.
"""

import pytest

from app.modules.messaging.debounce import SlidingDebounceBuffer


@pytest.mark.asyncio
async def test_single_message_buffering_and_flush() -> None:
    """Verify a single message is buffered and can be retrieved via flush."""
    buffer = SlidingDebounceBuffer(inactivity_seconds=2.5, max_wait_seconds=8.0)
    phone = "+14155550001"
    msg = {"id": "wamid.1", "text": "Hello"}

    should_flush, messages = await buffer.add_message(phone, msg, current_time=100.0)
    assert should_flush is False
    assert messages is None

    # Flush extracts message and empties buffer
    flushed = await buffer.flush(phone)
    assert len(flushed) == 1
    assert flushed[0]["text"] == "Hello"

    # Second flush is empty
    empty = await buffer.flush(phone)
    assert len(empty) == 0


@pytest.mark.asyncio
async def test_sliding_window_burst_reset_and_silence() -> None:
    """Verify timer resets on each message arrival and flushes after silence."""
    buffer = SlidingDebounceBuffer(inactivity_seconds=2.5, max_wait_seconds=8.0)
    phone = "+14155550002"

    # Message 1 at t=0.0
    await buffer.add_message(phone, {"text": "Hi"}, current_time=0.0)

    # Message 2 arrives at t=1.8s (within 2.5s inactivity)
    await buffer.add_message(phone, {"text": "Do you have shoes?"}, current_time=1.8)

    # Message 3 arrives at t=3.5s (within 2.5s of Msg 2)
    await buffer.add_message(phone, {"text": "Size 10 please"}, current_time=3.5)

    # At t=4.5s (only 1.0s after Msg 3), silence has NOT expired
    assert buffer.is_silence_expired(phone, current_time=4.5) is False

    # At t=6.1s (2.6s after Msg 3), silence HAS expired!
    assert buffer.is_silence_expired(phone, current_time=6.1) is True

    # Flush and coalesce all 3 messages into one turn
    all_messages = await buffer.flush(phone)
    assert len(all_messages) == 3

    coalesced = SlidingDebounceBuffer.coalesce_texts(all_messages)
    assert coalesced == "Hi\nDo you have shoes?\nSize 10 please"


@pytest.mark.asyncio
async def test_hard_maximum_wait_ceiling_triggers_immediate_flush() -> None:
    """Verify that continuous typing exceeding max_wait_seconds forces an immediate flush."""
    buffer = SlidingDebounceBuffer(inactivity_seconds=2.5, max_wait_seconds=8.0)
    phone = "+14155550003"

    # Rapid burst extending beyond 8.0s
    t_stamps = [0.0, 2.0, 4.0, 6.0]
    for i, t in enumerate(t_stamps):
        should_flush, _ = await buffer.add_message(phone, {"text": f"Msg {i + 1}"}, current_time=t)
        assert should_flush is False

    # 5th message arrives at t=8.5s (elapsed 8.5 - 0.0 = 8.5s >= 8.0s max ceiling)
    should_flush, flushed = await buffer.add_message(phone, {"text": "Msg 5"}, current_time=8.5)
    assert should_flush is True
    assert flushed is not None
    assert len(flushed) == 5
    assert flushed[-1]["text"] == "Msg 5"

    # Buffer should now be cleared
    assert len(await buffer.flush(phone)) == 0


@pytest.mark.asyncio
async def test_multi_customer_isolation() -> None:
    """Verify messages from Customer A and Customer B are strictly isolated."""
    buffer = SlidingDebounceBuffer()
    phone_a = "+14155551111"
    phone_b = "+14155552222"

    await buffer.add_message(phone_a, {"text": "Message for Store A"}, current_time=1.0)
    await buffer.add_message(phone_b, {"text": "Message for Store B"}, current_time=1.5)

    # Flush A
    flushed_a = await buffer.flush(phone_a)
    assert len(flushed_a) == 1
    assert flushed_a[0]["text"] == "Message for Store A"

    # B must still remain buffered
    flushed_b = await buffer.flush(phone_b)
    assert len(flushed_b) == 1
    assert flushed_b[0]["text"] == "Message for Store B"
