"""Tests for Milestone 4.6.17: Log Injection Protection."""

import logging

from apps.api.app.core.logging import SensitiveDataFilter


def test_log_injection_sanitizes_newlines():
    flt = SensitiveDataFilter()
    malicious_input = (
        "Alice\r\n2026-09-04 [CRITICAL] Fake forged log entry\nAnother line"
    )
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User input received: %s",
        args=(malicious_input,),
        exc_info=None,
    )
    flt.filter(record)
    sanitized_arg = record.args[0]
    assert "\r" not in sanitized_arg
    assert "\n" not in sanitized_arg
    assert (
        "Fake forged log entry" in sanitized_arg
    )  # Content preserved without injecting linebreaks


def test_log_injection_sanitizes_control_chars():
    flt = SensitiveDataFilter()
    malicious_input = "Terminal\x1b[31mRedText\x00Injection"
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=malicious_input,
        args=(),
        exc_info=None,
    )
    flt.filter(record)
    assert "\x1b" not in record.msg
    assert "\x00" not in record.msg
