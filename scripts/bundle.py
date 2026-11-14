"""Cross-platform `make bundle`: stage a deployable Databricks App in build/app (works on Windows without make).

  python scripts/bundle.py              # expects app/frontend/dist (run `npm run build` in app/frontend first)

Then:
  databricks sync build/app /Workspace/Users/<you>/fixit-madison-app --full -p fixit
  databricks apps deploy fixit-madison --source-code-path /Workspace/Users/<you>/fixit-madison-app -p fixit
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "app"


def main() -> int:
    dist = ROOT / "app" / "frontend" / "dist"
    if not (dist / "index.html").exists():
        print("app/frontend/dist missing: run `npm run build` in app/frontend first.")
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "tests")
    shutil.copytree(ROOT / "app" / "backend", OUT / "backend", ignore=ignore)
    shutil.copy2(ROOT / "app" / "app.yaml", OUT / "app.yaml")
    shutil.copy2(ROOT / "app" / "requirements.txt", OUT / "requirements.txt")
    shutil.copytree(dist, OUT / "static")
    shutil.copytree(ROOT / "demo" / "cached_outputs", OUT / "demo" / "cached_outputs")
    # Never ship local secrets or data.
    for bad in (".env", "data"):
        assert not (OUT / bad).exists(), bad
    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Staged {files} files in {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
