# C01 — First real client runbook

This is the operational checklist for the first paid supplier-file jobs.

## 0. Confirm scope and payment

Before processing anything, confirm in writing:

- one supplier / agreed file set;
- CSV or XLSX;
- agreed SKU limit;
- target WooCommerce format;
- pilot price;
- no automatic publication to production;
- who can approve ambiguous data rules.

For early pilots, a practical default is **50% upfront / 50% before delivery**. Full upfront is even better if the client accepts it.

## 1. Preserve the source

Create a local client folder:

```text
client-name/
  00_original/
  10_working/
  20_output/
  30_notes/
```

Never edit the original supplier file. Never commit client files to GitHub.

## 2. Inspect before changing anything

Record:

- workbook and sheet name;
- header row;
- row count;
- source headers;
- SKU field and whether Excel stores it as text or number;
- price basis (HT/TTC);
- stock semantics;
- variation structure;
- packaging/unit semantics;
- GTIN/EAN field;
- whether a previous supplier feed exists.

## 3. Create the mapping

Map only fields actually present in the file:

```text
supplier column -> canonical field -> WooCommerce field
```

Do not invent SKU, price, stock, GTIN/EAN, VAT, identifiers or product attributes.

## 4. Run the first pass without guessing

Normalize and validate the file.

Classify anomalies as:

- **ERROR** — unsafe to import;
- **REVIEW** — needs a client/human decision;
- **WARNING** — can continue, but should be reported.

The purpose of the first pass is to discover questions, not to force every row through the importer.

## 5. Ask one consolidated question email

Reference exact SKUs and source rows. Group all ambiguous items into one message instead of creating repeated back-and-forth.

Typical questions:

- What does `RUPTURE` mean in the stock column?
- Does blank stock mean 0, unchanged, or unknown?
- Does `x6` mean six pieces?
- Is a numeric Excel SKU displayed with leading zeros the real SKU?
- Which of two duplicate SKU rows is correct?
- What is the correct price / GTIN / variation attribute for an invalid row?

## 6. Record every client decision

Every confirmed answer becomes an explicit rule for that supplier/client.

Examples:

```text
RUPTURE -> stock 0
blank stock -> stock 0
x6 -> 6 pieces
Excel value 721 -> confirmed SKU 000721
```

Keep the raw source value traceable to the original file.

## 7. Rerun

After receiving the answers:

1. normalize;
2. validate;
3. compare previous/current feeds when available;
4. generate `woocommerce_ready.csv`;
5. generate `report.xlsx`.

If unresolved ERROR/REVIEW rows remain, keep them out of the import rather than guessing.

## 8. QA before delivery

Check at minimum:

- input/output row counts;
- blocked rows are absent from the WooCommerce CSV;
- leading-zero SKUs are preserved;
- no duplicate SKU remains;
- GTIN/EAN formats and duplicates;
- prices and decimal separators;
- stock 0 vs blank;
- parent/variation relationships;
- suspicious large price/stock changes;
- WooCommerce CSV headers and UTF-8 encoding.

Never import to production during an early pilot unless this was separately agreed.

## 9. Deliver

Send the client:

1. `woocommerce_ready.csv`;
2. `report.xlsx`;
3. a short summary of what changed and any remaining caveats.

Keep the supplier mapping and approved rules internally for the next file.

## 10. Measure the business

For every job log:

- intake/inspection time;
- mapping time;
- number of client questions;
- number of manual corrections;
- total delivery time;
- price paid;
- whether the client sends a second file.

The main milestone is not the first delivery. It is a **repeat paid file that takes much less time to process**.
