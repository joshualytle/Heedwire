"""Shared HTTP session: explicit timeouts + retry/backoff on transient errors."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter, Retry

DEFAULT_TIMEOUT = 30


def session(user_agent: str = "Heedwire/0.1") -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({"User-Agent": user_agent})
    return s


def get_json(url: str, *, params: dict | None = None, timeout: int = DEFAULT_TIMEOUT,
             sess: requests.Session | None = None) -> dict:
    s = sess or session()
    resp = s.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
