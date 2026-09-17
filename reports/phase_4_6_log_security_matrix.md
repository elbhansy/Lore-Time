# Phase 4.6 — Log Security Matrix

## 1. Overview
This matrix audits data classifications across all application and system logs, validating the redaction of secrets, sanitization of user-controlled inputs, and complete suppression of future story content (spoiler firewall).

---

## 2. Classification Matrix

| Data Category | Allowed | Redacted | Forbidden | Tested | Implementation / Enforcement Mechanism | Status |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Passwords & API Keys** | No | Yes | Yes | Yes | `SensitiveDataFilter.KEY_VALUE_SECRET_REGEX` masks values with `****` | **SECURED** |
| **Database URL Credentials** | No | Yes | Yes | Yes | `SensitiveDataFilter.PASSWORD_URL_REGEX` replaces `:password@` with `:****@` | **SECURED** |
| **Authorization / Bearer Tokens** | No | Yes | Yes | Yes | `SensitiveDataFilter.AUTH_BEARER_REGEX` masks tokens with `Bearer ****` | **SECURED** |
| **Cookies & Session IDs** | No | Yes | Yes | Yes | `SensitiveDataFilter.COOKIE_REGEX` masks cookie values; request bodies excluded | **SECURED** |
| **Raw SQL Statements** | No | No | Yes | Yes | SQLAlchemy parameterization; SQL masked in error handlers and logs | **SECURED** |
| **Stack Traces in API Responses** | No | No | Yes | Yes | Client receives generic JSON; stack traces strictly internal (logger.error) | **SECURED** |
| **Raw HTTP Request Bodies** | No | No | Yes | Yes | Request middleware only captures path, method, and duration_ms | **SECURED** |
| **Future Story Lore (Chapter > N)** | No | No | Yes | Yes | Domain filtering; logs record requested bounds without future text | **SECURED** |
| **Series Data Identifiers** | Yes | No | No | Yes | UUIDs allowed in logs for tenant correlation and auditing | **SECURED** |
| **User-Controlled Strings** | Yes | Yes | No | Yes | `SensitiveDataFilter.CONTROL_CHAR_REGEX` strips newlines & control chars | **SECURED** |
| **Standardized Error Codes** | Yes | No | No | Yes | Canonical codes (`RESOURCE_NOT_FOUND`, `INVALID_CHAPTER`, etc.) logged | **SECURED** |

---

## 3. Log Injection Defenses
- **Newline Injection**: `\r` and `\n` characters inside input strings are replaced with whitespace. Fake log line forging is completely blocked.
- **Terminal Control Sequences**: ANSI color codes, backspaces, and NULL bytes (`\x00`, `\x1b`) are sanitized before log record emission.
- **Request ID Bounding**: Client-supplied `X-Request-ID` is verified against `^[A-Za-z0-9\-_]{1,64}$`. Malformed IDs are discarded and replaced with random UUIDv4.
