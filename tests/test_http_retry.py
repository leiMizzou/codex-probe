"""Tests for the HTTP retry policy. Uses monkey-patched urlopen — no real network."""

from __future__ import annotations

import io
import os
import sys
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import provider_probe as pp


class _FakeResp:
    def __init__(self, status: int, body: bytes, headers: dict | None = None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class HttpRetryTests(unittest.TestCase):
    def setUp(self):
        self.calls: list[tuple[str, str]] = []
        self.actions: list = []  # queue of _FakeResp or Exception
        self._orig_urlopen = urllib.request.urlopen

        def fake_urlopen(req, timeout=120):
            self.calls.append((req.full_url, req.get_method()))
            if not self.actions:
                raise AssertionError("unexpected extra urlopen call")
            action = self.actions.pop(0)
            if isinstance(action, BaseException):
                raise action
            return action

        urllib.request.urlopen = fake_urlopen
        self.provider = pp.Provider("test", "https://example.com/v1", "sk-test", "gpt-5.5")
        self.runtime = pp.RuntimeOptions(pp.DEFAULT_PRICES_PER_M.copy(), http_retries=2, http_retry_delay=0)

    def tearDown(self):
        urllib.request.urlopen = self._orig_urlopen

    @staticmethod
    def _httperror(code: int, body: bytes = b'{"error":"x"}'):
        return urllib.error.HTTPError("https://example.com", code, "msg", {}, io.BytesIO(body))

    def test_success_first_try_no_retry_field(self):
        self.actions = [_FakeResp(200, b'{"ok": true}')]
        result = pp.http(self.provider, "GET", "/foo", runtime=self.runtime)
        self.assertTrue(result["ok"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["retries_used"], 0)

    def test_retry_on_5xx_then_success(self):
        self.actions = [self._httperror(503, b'{"down":true}'), _FakeResp(200, b'{"ok": true}')]
        result = pp.http(self.provider, "GET", "/foo", runtime=self.runtime)
        self.assertTrue(result["ok"])
        self.assertEqual(result.get("retries_used"), 1)
        self.assertEqual(result.get("attempts"), 2)
        self.assertEqual(len(self.calls), 2)

    def test_no_retry_on_4xx(self):
        self.actions = [self._httperror(401, b'{"error":"bad key"}')]
        result = pp.http(self.provider, "GET", "/foo", runtime=self.runtime)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], 401)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["retries_used"], 0)

    def test_retry_exhausted_returns_last_error(self):
        self.actions = [self._httperror(500, b"oops")] * 3  # initial + 2 retries
        result = pp.http(self.provider, "GET", "/foo", runtime=self.runtime)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], 500)
        self.assertEqual(result.get("retries_used"), 2)
        self.assertEqual(result.get("attempts"), 3)
        self.assertEqual(len(self.calls), 3)

    def test_retry_on_transport_error(self):
        self.actions = [TimeoutError("read timeout"), _FakeResp(200, b'{"ok": true}')]
        result = pp.http(self.provider, "GET", "/foo", runtime=self.runtime)
        self.assertTrue(result["ok"])
        self.assertEqual(result.get("retries_used"), 1)

    def test_no_retry_when_disabled(self):
        runtime = pp.RuntimeOptions(pp.DEFAULT_PRICES_PER_M.copy(), http_retries=0, http_retry_delay=0)
        self.actions = [self._httperror(500, b"oops")]
        result = pp.http(self.provider, "GET", "/foo", runtime=runtime)
        self.assertFalse(result["ok"])
        self.assertEqual(len(self.calls), 1)

    def test_post_does_not_retry_by_default(self):
        self.actions = [self._httperror(500, b"oops")]
        result = pp.http(self.provider, "POST", "/chat/completions", {"x": 1}, runtime=self.runtime)
        self.assertFalse(result["ok"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(self.calls), 1)

    def test_post_can_retry_when_explicitly_enabled(self):
        runtime = pp.RuntimeOptions(
            pp.DEFAULT_PRICES_PER_M.copy(),
            http_retries=2,
            http_retry_delay=0,
            retry_non_idempotent=True,
        )
        self.actions = [self._httperror(500, b"oops"), _FakeResp(200, b'{"ok": true}')]
        result = pp.http(self.provider, "POST", "/chat/completions", {"x": 1}, runtime=runtime)
        self.assertTrue(result["ok"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["retries_used"], 1)


if __name__ == "__main__":
    unittest.main()
