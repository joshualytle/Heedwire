from heedwire.config import Watch
from heedwire.taxonomy import Entry, resolve


def _entries():
    return [
        Entry(id="fortinet.fortios", vendor="Fortinet", category="Network Security / Firewalls",
              cpe_vendor="fortinet", cpe_product="fortios", aliases=["FortiOS"], alias_safety="exact",
              advisory_feed="https://example/forti.rss"),
        Entry(id="vmware.esxi", vendor="VMware", category="Hypervisors",
              cpe_vendor="vmware", cpe_product="esxi", aliases=["ESXi"], alias_safety="exact"),
    ]


def test_resolve_by_product():
    rw = resolve(Watch(products=["vmware.esxi"]), _entries())
    assert "vmware/esxi" in rw.vendor_products
    assert "fortinet/fortios" not in rw.vendor_products


def test_resolve_by_vendor_adds_advisory_feed():
    rw = resolve(Watch(vendors=["fortinet"]), _entries())
    assert "fortinet/fortios" in rw.vendor_products
    assert "https://example/forti.rss" in rw.advisory_feeds
    assert ("fortios", "exact") in rw.aliases


def test_resolve_by_category():
    rw = resolve(Watch(categories=["Network Security / Firewalls"]), _entries())
    assert "fortinet/fortios" in rw.vendor_products


def test_custom_entry():
    rw = resolve(Watch(custom=[{"cpe": {"vendor": "acme", "product": "widget"},
                                "aliases": ["AcmeWidget"], "alias_safety": "phrase"}]), [])
    assert "acme/widget" in rw.vendor_products
    assert ("acmewidget", "phrase") in rw.aliases
