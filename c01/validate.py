from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from .models import CanonicalProduct, Issue, ValidationResult


ZERO_FORMAT_RE = re.compile(r"^0{2,}$")


def is_valid_gtin(value: str) -> bool:
    if not value.isdigit() or len(value) not in {8, 12, 13, 14}:
        return False
    digits = [int(ch) for ch in value]
    check_digit = digits[-1]
    body = digits[:-1]
    total = 0
    weight = 3
    for digit in reversed(body):
        total += digit * weight
        weight = 1 if weight == 3 else 3
    expected = (10 - (total % 10)) % 10
    return check_digit == expected


def _issue(product: CanonicalProduct, severity: str, code: str, field: str, raw_value: Any, message: str) -> Issue:
    return Issue(
        source=product.source,
        sku=product.sku,
        severity=severity,
        code=code,
        field=field,
        raw_value=raw_value,
        message=message,
    )


def validate_products(products: list[CanonicalProduct]) -> ValidationResult:
    issues: list[Issue] = []
    sku_counts = Counter(p.sku for p in products if p.sku)
    duplicate_skus = {sku for sku, count in sku_counts.items() if count > 1}

    ean_to_products: dict[str, list[CanonicalProduct]] = defaultdict(list)
    for product in products:
        if product.ean:
            ean_to_products[product.ean].append(product)

    for product in products:
        if not product.sku:
            issues.append(_issue(product, "ERROR", "MISSING_SKU", "sku", "", "SKU is required; row cannot be imported safely."))
        elif product.sku in duplicate_skus:
            issues.append(_issue(product, "ERROR", "DUPLICATE_SKU", "sku", product.sku, "SKU appears more than once in the same supplier file."))

        if product.flags.get("sku_numeric_cell"):
            number_format = str(product.flags.get("sku_number_format") or "")
            if ZERO_FORMAT_RE.match(number_format):
                issues.append(
                    _issue(
                        product,
                        "REVIEW",
                        "SKU_NUMERIC_FORMAT_RISK",
                        "sku",
                        product.sku or "",
                        f"SKU is stored as a numeric Excel cell with display format {number_format!r}; leading zeros may be presentation-only and require confirmation.",
                    )
                )
            else:
                issues.append(_issue(product, "WARNING", "SKU_NUMERIC_CELL", "sku", product.sku or "", "SKU is stored as a numeric Excel cell; text storage is safer."))

        if not product.name:
            issues.append(_issue(product, "ERROR", "MISSING_NAME", "name", "", "Product name is required."))

        if product.flags.get("price_parse_error"):
            issues.append(_issue(product, "ERROR", "INVALID_PRICE", "price", product.flags.get("raw_price", ""), "Price could not be parsed deterministically."))
        elif product.price is None:
            issues.append(_issue(product, "REVIEW", "MISSING_PRICE", "price", "", "Price is blank; confirm whether it should remain unchanged or be supplied."))
        elif product.price < 0:
            issues.append(_issue(product, "ERROR", "NEGATIVE_PRICE", "price", str(product.price), "Negative price is invalid."))
        elif product.price == 0:
            issues.append(_issue(product, "REVIEW", "ZERO_PRICE", "price", "0", "Zero price may be intentional but requires confirmation."))

        if product.flags.get("stock_parse_error"):
            issues.append(_issue(product, "REVIEW", "UNKNOWN_STOCK_VALUE", "stock", product.flags.get("raw_stock", ""), "Stock value is not an integer and no supplier-specific alias rule exists."))
        elif product.stock is None:
            issues.append(_issue(product, "REVIEW", "MISSING_STOCK", "stock", "", "Stock is blank; blank and zero are intentionally treated as different states."))
        elif product.stock < 0:
            issues.append(_issue(product, "ERROR", "NEGATIVE_STOCK", "stock", str(product.stock), "Negative stock is invalid for this demo workflow."))

        if not product.ean:
            issues.append(_issue(product, "WARNING", "MISSING_GTIN", "ean", "", "EAN/GTIN is blank."))
        elif not product.ean.isdigit() or len(product.ean) not in {8, 12, 13, 14}:
            issues.append(_issue(product, "WARNING", "INVALID_GTIN_FORMAT", "ean", product.ean, "GTIN must contain 8, 12, 13, or 14 digits."))
        elif not is_valid_gtin(product.ean):
            issues.append(_issue(product, "WARNING", "INVALID_GTIN_CHECKSUM", "ean", product.ean, "GTIN checksum is invalid."))

        if product.ean and len(ean_to_products[product.ean]) > 1:
            issues.append(_issue(product, "REVIEW", "DUPLICATE_GTIN", "ean", product.ean, "The same GTIN appears on multiple supplier rows. WooCommerce treats the global unique ID as unique, so confirm which row is correct before import."))

        if product.flags.get("packaging_parse_error"):
            issues.append(_issue(product, "REVIEW", "UNKNOWN_PACKAGING", "packaging", product.packaging_raw or "", "Packaging could not be normalized with the configured unit rules."))

        if product.flags.get("vat_parse_error"):
            issues.append(_issue(product, "WARNING", "INVALID_VAT", "vat_rate", product.flags.get("raw_vat_rate", ""), "VAT value could not be parsed."))
        elif product.vat_rate is not None and not (0 <= product.vat_rate <= 100):
            issues.append(_issue(product, "WARNING", "VAT_OUT_OF_RANGE", "vat_rate", str(product.vat_rate), "VAT is outside the expected 0-100 range."))

        if product.parent_sku:
            if not product.parent_name:
                issues.append(_issue(product, "REVIEW", "MISSING_PARENT_NAME", "parent_name", "", "Variation has a parent SKU but no confirmed parent product name."))
            if not product.color and not product.size:
                issues.append(_issue(product, "REVIEW", "MISSING_VARIATION_ATTRIBUTE", "variation", "", "Variation has no color or size value."))

    groups: dict[str, list[CanonicalProduct]] = defaultdict(list)
    for product in products:
        if product.parent_sku:
            groups[product.parent_sku].append(product)

    for parent_sku, members in groups.items():
        names = {p.parent_name for p in members if p.parent_name}
        categories = {p.category for p in members if p.category}
        if len(names) > 1:
            for product in members:
                issues.append(_issue(product, "REVIEW", "INCONSISTENT_PARENT_NAME", "parent_name", product.parent_name or "", f"Variation group {parent_sku} contains multiple parent names."))
        if len(categories) > 1:
            for product in members:
                issues.append(_issue(product, "REVIEW", "INCONSISTENT_PARENT_CATEGORY", "category", product.category or "", f"Variation group {parent_sku} contains multiple categories."))

        for attribute in ("color", "size"):
            present = [bool(getattr(product, attribute)) for product in members]
            if any(present) and not all(present):
                for product in members:
                    if not getattr(product, attribute):
                        issues.append(
                            _issue(
                                product,
                                "REVIEW",
                                "INCOMPLETE_VARIATION_ATTRIBUTE",
                                attribute,
                                "",
                                f"Variation group {parent_sku} uses {attribute} but this row is blank; confirm the intended variation structure.",
                            )
                        )

    return ValidationResult(issues=issues, duplicate_skus=duplicate_skus)
