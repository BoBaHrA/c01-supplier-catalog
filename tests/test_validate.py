from decimal import Decimal

from c01.models import CanonicalProduct, SourceRef
from c01.validate import is_valid_gtin, validate_products


def product(**overrides):
    base = dict(
        source=SourceRef("demo.xlsx", "Catalogue", 2),
        sku="000123",
        name="Demo",
        ean="3760000000015",
        price=Decimal("10.00"),
        stock=2,
        package_qty=Decimal("1"),
        package_unit="piece",
        packaging_raw="1 pc",
        category="Demo",
        parent_sku=None,
        parent_name=None,
        color=None,
        size=None,
        unit="pc",
        vat_rate=Decimal("20"),
        weight_kg=Decimal("0.2"),
        active=True,
        flags={},
    )
    base.update(overrides)
    return CanonicalProduct(**base)


def test_gtin_checksum():
    assert is_valid_gtin("4006381333931")
    assert not is_valid_gtin("4006381333932")


def test_duplicate_sku_blocks_both_rows():
    first = product()
    second = product(source=SourceRef("demo.xlsx", "Catalogue", 3))
    result = validate_products([first, second])
    duplicate_rows = {i.source.row for i in result.issues if i.code == "DUPLICATE_SKU"}
    assert duplicate_rows == {2, 3}


def test_blank_stock_requires_review_not_zero():
    result = validate_products([product(stock=None)])
    assert any(i.code == "MISSING_STOCK" and i.severity == "REVIEW" for i in result.issues)
