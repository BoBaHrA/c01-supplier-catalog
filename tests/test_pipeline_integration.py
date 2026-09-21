from pathlib import Path

from c01.demo_data import generate_demo_files
from c01.pipeline import run


def test_demo_pipeline_end_to_end(tmp_path):
    root = Path(__file__).resolve().parents[1]
    demo_dir = tmp_path / "demo"
    previous, current = generate_demo_files(root / "data/demo", demo_dir)

    summary = run(
        previous,
        current,
        root / "config/supplier_demo.yaml",
        tmp_path / "output",
    )

    assert summary["supplier_rows"] == 47
    assert summary["errors"] == 5
    assert summary["review"] == 11
    assert summary["blocked_rows"] == 14
    assert summary["exported_rows"] == 37

    csv_text = (tmp_path / "output/woocommerce_ready.csv").read_text(encoding="utf-8")
    assert "simple,000101," in csv_text
    assert "variation,001006," not in csv_text
    assert ",721," not in csv_text
    assert (tmp_path / "output/report.xlsx").exists()
