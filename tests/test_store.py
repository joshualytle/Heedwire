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


def test_severity_estimated_round_trips(tmp_path):
    s = Store(tmp_path / "t.db")
    s.upsert(Item(source="rss:psirt-0", uid="A", title="t", url="u",
                  severity=Severity.HIGH, severity_estimated=True))
    got = s.unnotified()[0]
    assert got.severity is Severity.HIGH and got.severity_estimated is True
    s.close()
