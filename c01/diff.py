from __future__ import annotations

from collections import Counter
from decimal import Decimal

from .models import CanonicalProduct, Change


def _fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _package(product: CanonicalProduct) -> str:
    if product.package_qty is None or product.package_unit is None:
        return ""
    qty = format(product.package_qty, "f")
    if "." in qty:
        qty = qty.rstrip("0").rstrip(".")
    return f"{qty} {product.package_unit}"


def _unique_index(products: list[CanonicalProduct]) -> tuple[dict[str, CanonicalProduct], set[str]]:
    counts = Counter(p.sku for p in products if p.sku)
    duplicates = {sku for sku, count in counts.items() if count > 1}
    return ({p.sku: p for p in products if p.sku and p.sku not in duplicates}, duplicates)


def compare_catalogs(previous: list[CanonicalProduct], current: list[CanonicalProduct]) -> tuple[list[Change], int]:
    prev, _ = _unique_index(previous)
    curr, _ = _unique_index(current)
    previous_presence = {p.sku for p in previous if p.sku}
    current_presence = {p.sku for p in current if p.sku}
    changes: list[Change] = []
    unchanged = 0

    for sku in sorted(current_presence - previous_presence):
        product = curr.get(sku)
        if product:
            changes.append(Change(sku, "NEW_PRODUCT", "", "", "", None, product.source.row, "Present in current feed only."))

    for sku in sorted(previous_presence - current_presence):
        product = prev.get(sku)
        if product:
            changes.append(Change(sku, "REMOVED_FROM_FEED", "", "", "", product.source.row, None, "Missing from current feed; this does not mean delete from WooCommerce."))

    tracked = [
        ("price", lambda p: p.price),
        ("stock", lambda p: p.stock),
        ("packaging", _package),
        ("ean", lambda p: p.ean),
        ("name", lambda p: p.name),
        ("category", lambda p: p.category),
        ("parent_sku", lambda p: p.parent_sku),
        ("color", lambda p: p.color),
        ("size", lambda p: p.size),
    ]

    for sku in sorted(set(prev) & set(curr)):
        old = prev[sku]
        new = curr[sku]
        product_changed = False
        for field, getter in tracked:
            old_value = getter(old)
            new_value = getter(new)
            if old_value != new_value:
                product_changed = True
                changes.append(
                    Change(
                        sku=sku,
                        change_type=f"{field.upper()}_CHANGED",
                        field=field,
                        old_value=_fmt(old_value),
                        new_value=_fmt(new_value),
                        previous_row=old.source.row,
                        current_row=new.source.row,
                    )
                )
        if not product_changed:
            unchanged += 1

    return changes, unchanged
