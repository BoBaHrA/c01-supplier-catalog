from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from c01.demo_data import generate_demo_files


if __name__ == "__main__":
    previous, current = generate_demo_files(ROOT / "data" / "demo")
    print(f"Created {previous}")
    print(f"Created {current}")
