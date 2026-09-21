from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SourceRef:
    file: str
    sheet: str
    row: int


@dataclass
class RawRow:
    source: SourceRef
    values: dict[str, Any]
    cell_meta: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class NormalizationRecord:
    source: SourceRef
    sku: str | None
    field: str
    raw_value: Any
    normalized_value: Any
    rule: str


@dataclass
class CanonicalProduct:
    source: SourceRef
    sku: str | None
    name: str | None
    ean: str | None
    price: Decimal | None
    stock: int | None
    package_qty: Decimal | None
    package_unit: str | None
    packaging_raw: str | None
    category: str | None
    parent_sku: str | None
    parent_name: str | None
    color: str | None
    size: str | None
    unit: str | None
    vat_rate: Decimal | None
    weight_kg: Decimal | None
    active: bool | None
    flags: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Issue:
    source: SourceRef
    sku: str | None
    severity: str
    code: str
    field: str
    raw_value: Any
    message: str


@dataclass(frozen=True)
class Change:
    sku: str
    change_type: str
    field: str
    old_value: str
    new_value: str
    previous_row: int | None
    current_row: int | None
    note: str = ""


@dataclass
class ValidationResult:
    issues: list[Issue]
    duplicate_skus: set[str]

    @property
    def blocked_rows(self) -> set[int]:
        return {
            issue.source.row
            for issue in self.issues
            if issue.severity in {"ERROR", "REVIEW"}
        }
