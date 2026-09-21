# C01 Supplier Catalog — validation prototype

C01 is a deliberately small **service-first** prototype for preparing supplier catalogs for WooCommerce.

The goal is not to build a SaaS before demand is proven. A client sends an awkward supplier XLSX/CSV; the operator returns a checked WooCommerce-ready CSV plus a clear audit report. The commercial milestone is a **paid pilot**, then a **repeat paid file**.

## What V0 does

The demo works with two supplier snapshots:

```text
source_previous.csv ─┐
                     ├─ generate demo XLSX
source_current.csv  ─┘
                         ↓
supplier_previous.xlsx + supplier_current.xlsx
                         ↓
              parse → normalize → validate → diff
                         ↓
                woocommerce_ready.csv
                report.xlsx
```

The pipeline handles:

- SKU as text, including leading-zero preservation;
- detection of numeric Excel SKU cells that may only *display* leading zeros;
- `Decimal` price parsing instead of float arithmetic;
- comma/dot decimal separators and currency tokens;
- explicit distinction between blank stock and stock `0`;
- duplicate SKU detection;
- GTIN/EAN format, checksum and duplicate checks;
- normalized packaging units (`500 g` and `0,5 kg` compare as the same quantity);
- simple products and variable products with parent rows + variation rows;
- price, stock, packaging, GTIN, name, category and variation diffs;
- row-level traceability back to source file / sheet / Excel row;
- blocking `ERROR` / `REVIEW` rows from the WooCommerce CSV while allowing `WARNING` rows;
- an XLSX report with `SUMMARY`, `CHANGES`, `ERRORS`, `WARNINGS`, `REVIEWS`, and `NORMALIZATIONS` sheets.

Generated WooCommerce products are **drafts** (`Published = -1`). Nothing is sent to a live shop automatically.

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/generate_demo_xlsx.py
python -m c01.pipeline `
  --previous data/demo/supplier_previous.xlsx `
  --current data/demo/supplier_current.xlsx `
  --config config/supplier_demo.yaml `
  --output output
pytest -q
```

Linux/macOS equivalent:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_demo_xlsx.py
python -m c01.pipeline \
  --previous data/demo/supplier_previous.xlsx \
  --current data/demo/supplier_current.xlsx \
  --config config/supplier_demo.yaml \
  --output output
pytest -q
```

Expected output:

```text
output/woocommerce_ready.csv
output/report.xlsx
```

## Demo data

`data/demo/source_previous.csv` and `data/demo/source_current.csv` are synthetic source data used to generate the two realistic supplier XLSX files. The demo intentionally contains leading-zero SKUs, a numeric SKU displayed as `000000`, duplicate/blank SKUs, comma prices, invalid and blank values, zero/blank/unknown/negative stock, GTIN problems, new and removed products, price/stock/packaging changes, equivalent unit conversions, variable products, incomplete variations, and extra whitespace.

The generated `.xlsx` files are ignored by Git because they are reproducible from the source CSVs.

## Supplier mapping

Supplier-specific mapping lives in `config/supplier_demo.yaml` rather than being hardcoded into the business logic. For the first paid file, the intended workflow is to copy this config and explicitly confirm the client's mapping/rules rather than trying to infer every field automatically.

## Safety rules in V0

The pipeline intentionally does **not** guess critical commerce data.

- Unknown SKU stays unknown.
- Invalid price is not repaired by AI.
- `stock = "rupture"` is not silently converted to `0` unless a supplier-specific rule is explicitly agreed.
- Blank stock and zero stock are different states.
- A product missing from the current supplier feed is reported as `REMOVED_FROM_FEED`; it is **not** automatically deleted from WooCommerce.
- Rows requiring a business decision are excluded from the ready CSV and appear in `REVIEWS`.
- No WooCommerce API, SFTP, scheduled publishing, billing, user accounts, or dashboard exists in V0.

### Price / VAT caveat

The demo supplier column is `Prix HT`. V0 exports that numeric price unchanged to `Regular price`; it does **not** invent VAT math. Before processing a real store, confirm whether the WooCommerce shop is configured to enter/display prices including or excluding tax and agree on the required output basis.

## Repository data policy

The repository may contain only synthetic demo files and code. Real client supplier feeds, exports, reports, credentials, URLs containing secrets, and production dumps must never be committed. `.gitignore` excludes client-data directories and generated output.

## Scope discipline

The next milestone is **not a UI**. It is: prove the demo works, show it to relevant WooCommerce studios/shops, obtain a real supplier file, agree a fixed pilot price, get paid, deliver safely, and see whether the client returns with a second file. Only repeated paid work justifies more automation.
