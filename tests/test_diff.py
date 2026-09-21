from decimal import Decimal

from c01.diff import compare_catalogs
from c01.models import CanonicalProduct, SourceRef


def product(sku, row, price="10", stock=5, packaging=(Decimal("1"), "piece")):
    return CanonicalProduct(
        source=SourceRef("demo.xlsx", "Catalogue", row),
        sku=sku,
        name="Demo",
        ean=None,
        price=Decimal(price),
        stock=stock,
        package_qty=packaging[0],
        package_unit=packaging[1],
        packaging_raw="1 pc",
        category="Demo",
        parent_sku=None,
        parent_name=None,
        color=None,
        size=None,
        unit="pc",
        vat_rate=Decimal("20"),
        weight_kg=None,
        active=True,
        flags={},
    )


def test_new_removed_and_field_changes():
    previous = [product("001", 2), product("002", 3)]
    current = [product("001", 2, price="11", stock=0), product("003", 4)]
    changes, unchanged = compare_catalogs(previous, current)
    types = {c.change_type for c in changes}
    assert {"NEW_PRODUCT", "REMOVED_FROM_FEED", "PRICE_CHANGED", "STOCK_CHANGED"}.issubset(types)
    assert unchanged == 0


def test_equivalent_packaging_does_not_create_change():
    previous = [product("001", 2, packaging=(Decimal("500"), "g"))]
    current = [product("001", 2, packaging=(Decimal("500.0"), "g"))]
    changes, unchanged = compare_catalogs(previous, current)
    assert not changes
    assert unchanged == 1
