"""Tests for Milestone 4.6.18: Secret Redaction in Logs."""

import logging

from apps.api.app.core.logging import SensitiveDataFilter


def test_sensitive_data_filter_masks_db_password():
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Connected to postgresql+psycopg://user:super_secret_pw@localhost:5432/db",
        args=(),
        exc_info=None,
    )
    flt.filter(record)
    assert "super_secret_pw" not in record.msg
    assert ":****@" in record.msg


def test_sensitive_data_filter_masks_bearer_token():
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Handling request with header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz",
        args=(),
        exc_info=None,
    )
    flt.filter(record)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in record.msg
    assert "Bearer ****" in record.msg


def test_sensitive_data_filter_masks_query_secrets():
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Login attempt with password=super_secret_pass and api_key=key_12345",
        args=(),
        exc_info=None,
    )
    flt.filter(record)
    assert "super_secret_pass" not in record.msg
    assert "key_12345" not in record.msg
    assert "password=****" in record.msg
    assert "api_key=****" in record.msg
