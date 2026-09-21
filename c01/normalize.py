from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import CanonicalProduct, NormalizationRecord, RawRow


SPACE_RE = re.compile(r"\s+")
INTEGER_RE = re.compile(r"^[+-]?\d+$")
DECIMAL_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
PACKAGING_RE = re.compile(r"^([+-]?\d+(?:[.,]\d+)?)\s*([A-Za-zÀ-ÿ]+)$", re.IGNORECASE)


def _display(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = SPACE_RE.sub(" ", str(value).strip())
    return text or None


def parse_decimal(value: Any, currency_tokens: list[str] | None = None) -> tuple[Decimal | None, bool]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, False
    if isinstance(value, Decimal):
        return value, False
    if isinstance(value, bool):
        return None, True
    if isinstance(value, int):
        return Decimal(value), False
    if isinstance(value, float):
        return Decimal(str(value)), False

    text = str(value).strip().replace("\u00a0", " ")
    for token in currency_tokens or []:
        text = text.replace(token, "")
    text = text.replace(" ", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    if not DECIMAL_RE.match(text):
        return None, True
    try:
        return Decimal(text), False
    except InvalidOperation:
        return None, True


def parse_stock(value: Any) -> tuple[int | None, bool]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, False
    if isinstance(value, bool):
        return None, True
    if isinstance(value, int):
        return value, False
    if isinstance(value, float):
        if value.is_integer():
            return int(value), False
        return None, True
    text = str(value).strip().replace(" ", "")
    if INTEGER_RE.match(text):
        return int(text), False
    return None, True


def parse_bool(value: Any) -> tuple[bool | None, bool]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, False
    if isinstance(value, bool):
        return value, False
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "oui", "o", "actif"}:
        return True, False
    if text in {"0", "false", "no", "non", "n", "inactif"}:
        return False, False
    return None, True


def parse_packaging(value: Any, unit_config: dict[str, list[str]]) -> tuple[Decimal | None, str | None, bool]:
    text = normalize_text(value)
    if text is None:
        return None, None, False
    match = PACKAGING_RE.match(text)
    if not match:
        return None, None, True

    qty, qty_error = parse_decimal(match.group(1))
    if qty_error or qty is None:
        return None, None, True
    raw_unit = match.group(2).lower()

    alias_to_unit: dict[str, str] = {}
    for canonical, aliases in unit_config.items():
        for alias in aliases:
            alias_to_unit[alias.lower()] = canonical

    unit = alias_to_unit.get(raw_unit)
    if unit is None:
        return None, None, True

    if unit == "kg":
        return qty * Decimal("1000"), "g", False
    if unit == "l":
        return qty * Decimal("1000"), "ml", False
    return qty, unit, False


def _record(records: list[NormalizationRecord], raw: RawRow, sku: str | None, field: str, before: Any, after: Any, rule: str) -> None:
    if _display(before) != _display(after):
        records.append(
            NormalizationRecord(
                source=raw.source,
                sku=sku,
                field=field,
                raw_value=before,
                normalized_value=after,
                rule=rule,
            )
        )


def normalize_row(raw: RawRow, config: dict[str, Any]) -> tuple[CanonicalProduct, list[NormalizationRecord]]:
    records: list[NormalizationRecord] = []
    flags: dict[str, Any] = {
        "raw_sku": raw.values.get("sku"),
        "raw_price": raw.values.get("price"),
        "raw_stock": raw.values.get("stock"),
        "raw_vat_rate": raw.values.get("vat_rate"),
    }

    raw_sku = raw.values.get("sku")
    sku_meta = raw.cell_meta.get("sku", {})
    if raw_sku is None or (isinstance(raw_sku, str) and not raw_sku.strip()):
        sku = None
    elif isinstance(raw_sku, bool):
        sku = str(raw_sku)
        flags["sku_numeric_cell"] = False
    elif isinstance(raw_sku, int):
        sku = str(raw_sku)
        flags["sku_numeric_cell"] = True
    elif isinstance(raw_sku, float) and raw_sku.is_integer():
        sku = str(int(raw_sku))
        flags["sku_numeric_cell"] = True
    else:
        sku = normalize_text(raw_sku)
        flags["sku_numeric_cell"] = False
    flags["sku_number_format"] = sku_meta.get("number_format", "")
    _record(records, raw, sku, "sku", raw_sku, sku, "trim/preserve-as-text")

    name = normalize_text(raw.values.get("name"))
    _record(records, raw, sku, "name", raw.values.get("name"), name, "trim/collapse-whitespace")

    ean_raw = raw.values.get("ean")
    ean = normalize_text(ean_raw)
    if ean is not None:
        cleaned = ean.replace(" ", "").replace("-", "")
        _record(records, raw, sku, "ean", ean_raw, cleaned, "remove-spaces-and-hyphens")
        ean = cleaned

    currency_tokens = config.get("normalization", {}).get("currency_tokens", [])
    price, price_error = parse_decimal(raw.values.get("price"), currency_tokens)
    flags["price_parse_error"] = price_error
    if not price_error:
        _record(records, raw, sku, "price", raw.values.get("price"), price, "decimal-normalization")

    stock, stock_error = parse_stock(raw.values.get("stock"))
    flags["stock_parse_error"] = stock_error
    if not stock_error:
        _record(records, raw, sku, "stock", raw.values.get("stock"), stock, "integer-normalization")

    packaging_raw = normalize_text(raw.values.get("packaging"))
    package_units = config.get("normalization", {}).get("packaging_units", {})
    package_qty, package_unit, packaging_error = parse_packaging(packaging_raw, package_units)
    flags["packaging_parse_error"] = packaging_error
    if not packaging_error and package_qty is not None and package_unit is not None and packaging_raw:
        match = PACKAGING_RE.match(packaging_raw)
        raw_unit = match.group(2).lower() if match else ""
        if raw_unit in {alias.lower() for key in ("kg", "l") for alias in package_units.get(key, [])}:
            qty_text = format(package_qty, "f")
            if "." in qty_text:
                qty_text = qty_text.rstrip("0").rstrip(".")
            canonical_packaging = f"{qty_text} {package_unit}"
            _record(records, raw, sku, "packaging", packaging_raw, canonical_packaging, "base-unit-normalization")

    category = normalize_text(raw.values.get("category"))
    parent_sku = normalize_text(raw.values.get("parent_sku"))
    parent_name = normalize_text(raw.values.get("parent_name"))
    color = normalize_text(raw.values.get("color"))
    size = normalize_text(raw.values.get("size"))
    unit = normalize_text(raw.values.get("unit"))

    vat_rate, vat_error = parse_decimal(raw.values.get("vat_rate"))
    flags["vat_parse_error"] = vat_error
    weight_kg, weight_error = parse_decimal(raw.values.get("weight_kg"))
    flags["weight_parse_error"] = weight_error
    active, active_error = parse_bool(raw.values.get("active"))
    flags["active_parse_error"] = active_error

    for field, normalized in (
        ("category", category),
        ("parent_sku", parent_sku),
        ("parent_name", parent_name),
        ("color", color),
        ("size", size),
        ("unit", unit),
    ):
        _record(records, raw, sku, field, raw.values.get(field), normalized, "trim/collapse-whitespace")

    return (
        CanonicalProduct(
            source=raw.source,
            sku=sku,
            name=name,
            ean=ean,
            price=price,
            stock=stock,
            package_qty=package_qty,
            package_unit=package_unit,
            packaging_raw=packaging_raw,
            category=category,
            parent_sku=parent_sku,
            parent_name=parent_name,
            color=color,
            size=size,
            unit=unit,
            vat_rate=vat_rate,
            weight_kg=weight_kg,
            active=active,
            flags=flags,
        ),
        records,
    )


def normalize_rows(rows: list[RawRow], config: dict[str, Any]) -> tuple[list[CanonicalProduct], list[NormalizationRecord]]:
    products: list[CanonicalProduct] = []
    records: list[NormalizationRecord] = []
    for raw in rows:
        product, product_records = normalize_row(raw, config)
        products.append(product)
        records.extend(product_records)
    return products, records
