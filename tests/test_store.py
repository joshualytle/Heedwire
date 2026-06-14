from heedwire.models import Item, Severity
from heedwire.store import Store


def test_upsert_dedup_and_notify(tmp_path):
    s = Store(tmp_path / "t.db")
    it = Item(source="kev", uid="CVE-1", title="x", url="u", severity=Severity.CRITICAL)
    assert s.upsert(it) is True          # new
    assert s.upsert(it) is False         # duplicate
    assert len(s.unnotified()) == 1
    s.mark_notified(["CVE-1"])
    assert s.unnotified() == []
    s.set_meta("last_run", "2026-01-01T00:00:00+00:00")
    assert s.get_meta("last_run") == "2026-01-01T00:00:00+00:00"
    s.close()
