"""Config loading: sane defaults, normalization, and secrets stay out of the file.

Guards the "secrets only from env" rule — the config carries an env-var *name*
(`url_env`), never a credential — plus watchlist normalization and gate parsing.
"""
from __future__ import annotations

from heedwire.config import load_config
from heedwire.models import Severity

FULL = """
sources:
  kev: { type: kev }
watch:
  categories: ["Network Security / Firewalls"]
  vendors: [Microsoft, Fortinet]
  products: [VMware.ESXi]
gates:
  min_severity: critical
  only_known_exploited: true
outputs:
  webhook: { type: webhook, url_env: HEEDWIRE_WEBHOOK_URL, format: slack }
lookback_hours: 48
"""


def _write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return load_config(p)


def test_defaults_on_empty_config(tmp_path):
    cfg = _write(tmp_path, "")
    assert cfg.gates.min_severity is Severity.UNKNOWN
    assert cfg.lookback_hours == 25 and cfg.api_host == "127.0.0.1"
    assert cfg.sources == {} and cfg.summarizer == {"enabled": False}


def test_watch_is_lowercased(tmp_path):
    cfg = _write(tmp_path, FULL)
    assert cfg.watch.vendors == ["microsoft", "fortinet"]
    assert cfg.watch.products == ["vmware.esxi"]
    assert cfg.watch.categories == ["Network Security / Firewalls"]   # categories kept as-is


def test_gates_parsed(tmp_path):
    cfg = _write(tmp_path, FULL)
    assert cfg.gates.min_severity is Severity.CRITICAL
    assert cfg.gates.only_known_exploited is True
    assert cfg.lookback_hours == 48


def test_secret_stays_in_env_only(tmp_path):
    """The config references an env-var name, never an actual secret/URL."""
    cfg = _write(tmp_path, FULL)
    spec = cfg.outputs["webhook"]
    assert spec["url_env"] == "HEEDWIRE_WEBHOOK_URL"
    # no credential/URL value is materialized from the file
    blob = repr(cfg).lower()
    assert "http://" not in blob and "https://" not in blob
