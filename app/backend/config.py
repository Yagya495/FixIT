"""Central configuration. Everything comes from env vars (.env is loaded if present)."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]   # .../app (in a deployed Databricks App this is the source root)
REPO_ROOT = APP_DIR.parent


def _load_dotenv() -> None:
    env = REPO_ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


DEMO_MODE = _bool("DEMO_MODE", True)
DATA_BACKEND = os.getenv("DATA_BACKEND", "local").strip().lower()
SHOW_BBOXES = _bool("SHOW_BBOXES", False)

# Databricks
def _normalize_host(h: str) -> str:
    """Databricks Apps may inject DATABRICKS_HOST as a bare hostname; URLs need the scheme."""
    h = h.strip().rstrip("/")
    return f"https://{h}" if h and not h.startswith(("http://", "https://")) else h


DATABRICKS_HOST = _normalize_host(os.getenv("DATABRICKS_HOST", ""))
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_CONFIG_PROFILE = os.getenv("DATABRICKS_CONFIG_PROFILE", "").strip()
DATABRICKS_WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
CATALOG = os.getenv("FIXIT_CATALOG", "fixit")

# Model endpoints — VERIFY with notebooks/00_smoke_tests.py and record the winners here / in .env
CHAT_ENDPOINT = os.getenv("CHAT_ENDPOINT", "databricks-llama-4-maverick")
VISION_ENDPOINT = os.getenv("VISION_ENDPOINT", "databricks-llama-4-maverick")
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
VECTOR_SEARCH_ENDPOINT = os.getenv("VECTOR_SEARCH_ENDPOINT", "fixit-vs")
VECTOR_INDEX = os.getenv("VECTOR_INDEX", f"{CATALOG}.silver.code_chunks_index")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")

LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "25"))

# Local storage
DATA_DIR = Path(os.getenv("FIXIT_DATA_DIR", REPO_ROOT / "data"))
SQLITE_PATH = DATA_DIR / "fixit.db"
LOCAL_EVIDENCE_DIR = DATA_DIR / "evidence"
EVIDENCE_VOLUME = f"/Volumes/{CATALOG}/raw/evidence"

# Deploy copies demo/ into app/demo (see Makefile `bundle`); locally it lives at the repo root.
DEMO_DIR = APP_DIR / "demo" if (APP_DIR / "demo").exists() else REPO_ROOT / "demo"
CACHE_DIR = DEMO_DIR / "cached_outputs"
STATIC_DIR = APP_DIR / "static" if (APP_DIR / "static").exists() else APP_DIR / "frontend" / "dist"

# Vision
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
MAX_FRAMES = 30
# Parallel vision calls within one upload request (frames are still stored in order).
VISION_CONCURRENCY = max(1, int(os.getenv("VISION_CONCURRENCY", "2")))

# Deadlines (FixIt defaults — NOT legal deadlines)
DEFAULT_WINDOW_HOURS = {"routine": 7 * 24, "urgent": 48, "emergency": 24}

# Calls (P1)
CALLS_ENABLED = _bool("CALLS_ENABLED", False)
CALL_ALLOWLIST = {n.strip() for n in os.getenv("CALL_ALLOWLIST", "").split(",") if n.strip()}
RETELL_API_KEY = os.getenv("RETELL_API_KEY", "").strip()
RETELL_AGENT_ID = os.getenv("RETELL_AGENT_ID", "").strip()
RETELL_FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER", "").strip()
# Separate from the provider key. Required because the demo app has no tenant authentication.
RETELL_OPERATOR_TOKEN = os.getenv("RETELL_OPERATOR_TOKEN", "").strip()

DISCLAIMER = (
    "FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center "
    "(608-257-0006) or City of Madison Building Inspection (608-266-4551)."
)

# Checked against the live City of Madison site on 2026-11-14 (see PROGRESS.md "Official sources"). The old
# /dpced/bi/report-a-problem/ URL silently redirected to the generic Building Inspection home page.
OFFICIAL_LINKS = {
    "chapter_27": "https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO",
    "building_inspection": "https://www.cityofmadison.com/dpced/building-inspection",
    "report_problem": "https://www.cityofmadison.com/dpced/building-inspection/file-a-complaint/interior-property",
    "complaint_process": "https://www.cityofmadison.com/dpced/building-inspection/file-a-complaint/process",
    "rent_abatement": "https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/rent-abatement",
    "retaliation": "https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/retaliation",
    "common_code_violations": "https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/common-code-violations",
    "tenant_resource_center": "https://www.tenantresourcecenter.org/",
}
