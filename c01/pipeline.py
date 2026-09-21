from __future__ import annotations

import argparse
from pathlib import Path

from .diff import compare_catalogs
from .export import export_report_xlsx, export_woocommerce_csv
from .io_excel import load_config, read_supplier_xlsx
from .normalize import normalize_rows
from .validate import validate_products


def run(previous_path: str | Path, current_path: str | Path, config_path: str | Path, output_dir: str | Path) -> dict[str, int]:
    config = load_config(config_path)
    previous_raw = read_supplier_xlsx(previous_path, config)
    current_raw = read_supplier_xlsx(current_path, config)

    previous, _ = normalize_rows(previous_raw, config)
    current, normalizations = normalize_rows(current_raw, config)
    validation = validate_products(current)
    changes, unchanged = compare_catalogs(previous, current)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "woocommerce_ready.csv"
    report_path = output_dir / "report.xlsx"

    exported_rows = export_woocommerce_csv(current, validation, config, csv_path)
    export_report_xlsx(report_path, current, validation, changes, unchanged, normalizations, exported_rows)

    summary = {
        "supplier_rows": len(current),
        "exported_rows": exported_rows,
        "blocked_rows": len(validation.blocked_rows),
        "errors": sum(i.severity == "ERROR" for i in validation.issues),
        "warnings": sum(i.severity == "WARNING" for i in validation.issues),
        "review": sum(i.severity == "REVIEW" for i in validation.issues),
        "changes": len(changes),
        "unchanged": unchanged,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a supplier catalog into a WooCommerce-ready CSV and audit report.")
    parser.add_argument("--previous", required=True, help="Previous supplier XLSX")
    parser.add_argument("--current", required=True, help="Current supplier XLSX")
    parser.add_argument("--config", default="config/supplier_demo.yaml", help="Supplier YAML mapping")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()

    summary = run(args.previous, args.current, args.config, args.output)
    print("C01 pipeline completed")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
