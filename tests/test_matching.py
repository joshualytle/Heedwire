from heedwire.config import Gates
from heedwire.matching import evaluate
from heedwire.models import Item, Severity
from heedwire.taxonomy import ResolvedWatch


def _item(**kw):
    base = dict(source="t", uid="u", title="t", url="x")
    base.update(kw)
    return Item(**base)


def test_structured_vendor_product():
    rw = ResolvedWatch(vendor_products={"fortinet/fortios"})
    it = _item(vendors=["fortinet"], products=["fortios"], severity=Severity.CRITICAL)
    f = evaluate(rw, Gates(), it)
    assert f and f.matched_rule == "structured"


def test_alias_exact_not_substring():
    rw = ResolvedWatch(aliases=[("esxi", "exact")])
    assert evaluate(rw, Gates(), _item(title="VMware ESXi flaw")) is not None
    assert evaluate(rw, Gates(), _item(title="esximore unrelated")) is None


def test_alias_cooccur_requires_security_term():
    rw = ResolvedWatch(aliases=[("windows", "cooccur")])
    assert evaluate(rw, Gates(), _item(title="Windows vulnerability patch")) is not None
    assert evaluate(rw, Gates(), _item(title="I like Windows wallpapers")) is None


def test_severity_gate_kev_bypass():
    rw = ResolvedWatch(vendor_products={"a/b"})
    low = _item(vendors=["a"], products=["b"], severity=Severity.LOW)
    assert evaluate(rw, Gates(min_severity=Severity.HIGH), low) is None
    kev = _item(vendors=["a"], products=["b"], severity=Severity.LOW, known_exploited=True)
    assert evaluate(rw, Gates(min_severity=Severity.HIGH), kev) is not None
