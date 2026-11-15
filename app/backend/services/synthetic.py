"""Synthetic Madison dataset generator (P0-12). Pure Python, deterministic given a seed and `now`.

Used by the local seeder (seed.py) and notebooks/05_generate_synthetic.py. Every person/owner is
fake; street names and neighborhoods are real Madison places. All rows carry is_synthetic / source.

Demo story (hand-crafted):
  - "1234 Demo St" (Langdon), owner "Isthmus Edge Properties (demo)", grade should land at D.
  - 6 HEAT reports at the demo building in the last 7 days (other households).
  - Owner has 3 other buildings with 11 open issues total.
"""
from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime, timedelta

from .taxonomy import VIOLATION_TYPES

DEMO_PROPERTY_ID = "P-DEMO-1234"
DEMO_OWNER_ID = "O-DEMO"
DEMO_ADDRESS = "1234 DEMO ST"

# Approximate neighborhood centroids (lat, lon, campus-ness weight, street names).
NEIGHBORHOODS = {
    "Langdon": (43.0766, -89.3960, 3.0, ["LANGDON ST", "N HENRY ST", "N CARROLL ST", "WISCONSIN AVE"]),
    "Mifflin": (43.0718, -89.3905, 2.5, ["W MIFFLIN ST", "W DAYTON ST", "N BASSETT ST", "N BROOM ST"]),
    "Regent": (43.0682, -89.4105, 2.0, ["REGENT ST", "ORCHARD ST", "MONROE ST", "VAN BUREN ST"]),
    "Vilas": (43.0605, -89.4100, 1.0, ["VILAS AVE", "JEFFERSON ST", "CHADBOURNE AVE", "MADISON ST"]),
    "Bay Creek": (43.0565, -89.3880, 1.0, ["S PARK ST", "GILSON ST", "CEDAR ST", "BEDFORD ST"]),
    "Tenney-Lapham": (43.0860, -89.3760, 1.0, ["E JOHNSON ST", "E GORHAM ST", "N BALDWIN ST", "SHERMAN AVE"]),
    "Marquette": (43.0880, -89.3640, 1.0, ["WILLIAMSON ST", "JENIFER ST", "SPAIGHT ST", "FAIR OAKS AVE"]),
    "Eken Park": (43.1020, -89.3560, 0.8, ["PACKERS AVE", "NORTH ST", "ELKA LN", "RUSKIN ST"]),
    "Allied Drive": (43.0330, -89.4500, 0.8, ["ALLIED DR", "JACOBS WAY", "CARLING DR", "REVIVAL RIDGE"]),
    "Greenbush": (43.0640, -89.3990, 1.2, ["MILTON ST", "ST JAMES CT", "PARK ST", "BROOKS ST"]),
    "Emerson East": (43.0955, -89.3650, 0.8, ["E DAYTON ST", "MAYFAIR AVE", "SCHLIMGEN AVE", "STARR AVE"]),
    "Southwest": (43.0420, -89.4700, 0.8, ["RAYMOND RD", "WHITNEY WAY", "MIDVALE BLVD", "PROSPECT PL"]),
}
CAMPUS = (43.0766, -89.4125)

FIRST = ["Badger", "Isthmus", "Mendota", "Monona", "Capitol", "Lakeview", "Willow", "Oak", "Cardinal", "Prairie",
         "Northstar", "Harbor", "Union", "Elm", "Summit", "Bluff", "Yahara", "Wingra", "Atwood", "Maple"]
SECOND = ["Properties", "Rentals", "Housing", "Living", "Realty", "Management", "Homes", "Apartments", "Group", "LLC"]
PEOPLE = ["A. Synth", "B. Fakename", "C. Example", "D. Placeholder", "E. Sample", "F. Demo", "G. Testperson"]

CATEGORY_OF = {v["type_id"]: v["category"] for v in VIOLATION_TYPES}
SEVERITY_OF = {v["type_id"]: v["default_severity"] for v in VIOLATION_TYPES}
TYPE_WEIGHTS = {
    "NO_HEAT": 10, "WATER_DAMAGE_MOLD": 14, "PEST_EVIDENCE": 12, "LEAK_PLUMBING": 12, "DAMAGED_SURFACES": 14,
    "BROKEN_LOCK": 7, "BROKEN_WINDOW": 8, "SMOKE_DETECTOR_MISSING": 8, "CO_DETECTOR_MISSING": 3,
    "EXPOSED_WIRING": 6, "BLOCKED_EGRESS": 3,
}


def unit_hash(property_id: str, unit: str) -> str:
    return hashlib.sha256(f"{property_id}:{unit}".encode()).hexdigest()[:12]


def _season_weight(type_id: str, month: int) -> float:
    if type_id == "NO_HEAT":
        return {12: 4.0, 1: 4.5, 2: 3.5, 11: 2.0, 3: 1.5}.get(month, 0.1)
    if type_id in ("WATER_DAMAGE_MOLD", "LEAK_PLUMBING"):
        return {3: 1.8, 4: 2.2, 5: 1.8, 6: 1.3}.get(month, 0.9)
    if type_id == "PEST_EVIDENCE":
        return {6: 1.6, 7: 1.8, 8: 1.6, 9: 1.3}.get(month, 0.8)
    return 1.0


def _pick_type(rng: random.Random, month: int) -> str:
    types = list(TYPE_WEIGHTS)
    w = [TYPE_WEIGHTS[t] * _season_weight(t, month) for t in types]
    return rng.choices(types, weights=w, k=1)[0]


def _severity(type_id: str, month: int) -> str:
    if type_id == "NO_HEAT":
        return "emergency" if (month >= 10 or month <= 5) else "urgent"
    return SEVERITY_OF[type_id]


# Every dataset is generated as of this fixed instant and then shifted so that "now" lands on the real clock.
# Why: date sampling below is seasonal (rejection-sampled by calendar month), so generating at the actual `now`
# made the number of random draws, and therefore every later draw, depend on the time of day. The demo owner's
# repair history came out different on each reset and its grade flipped between D and F. With a fixed reference the
# data is identical relative to `now` on every run; scoring code (landlords.py) is unchanged.
# Mid-November = the hackathon's heating season, so seasonality also looks right on demo day.
REFERENCE_NOW = datetime(2026, 11, 14, 12, 0, 0)
_TIME_FIELDS = ("reported_at", "fixed_at")


def generate(seed: int = 42, now: datetime | None = None, n_owners: int = 250, n_properties: int = 2000,
             n_reports: int = 12000, reference: datetime | None = REFERENCE_NOW) -> dict[str, list[dict]]:
    """Synthetic dataset relative to `now` (default: the current time).

    Deterministic: for a given seed, every time offset from `now` (report ages, repair durations, open/fixed status)
    is the same whatever `now` is. Pass reference=None to sample at `now` itself (old, time-dependent behavior).
    """
    now = (now or datetime.now()).replace(microsecond=0)
    ref = reference or now
    data = _generate_at(seed, ref, n_owners, n_properties, n_reports)
    shift = now - ref
    if shift:
        for r in data["reports"]:
            for f in _TIME_FIELDS:
                if r[f]:
                    r[f] = (datetime.fromisoformat(r[f]) + shift).isoformat(timespec="seconds")
    return data


def _generate_at(seed: int, now: datetime, n_owners: int, n_properties: int, n_reports: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    start = now - timedelta(days=3 * 365)

    # ---------------- owners
    owners, quality = [], {}
    used = set()
    for i in range(n_owners):
        while True:
            name = f"{rng.choice(FIRST)} {rng.choice(SECOND)}"
            if name not in used:
                used.add(name)
                break
            name = f"{name} {rng.randint(2, 99)}"
            if name not in used:
                used.add(name)
                break
        oid = f"O-{i:04d}"
        bad = rng.random() < 0.15
        quality[oid] = (rng.uniform(2.2, 3.5) if bad else rng.uniform(0.4, 1.2), bad)  # issue-rate multiplier
        mgmt = name if rng.random() < 0.6 else f"{rng.choice(FIRST)} Property Management"
        owners.append({"owner_id": oid, "name": f"{name} (synthetic)", "management_company": mgmt, "is_synthetic": 1})
    owners.append({"owner_id": DEMO_OWNER_ID, "name": "Isthmus Edge Properties (demo)",
                   "management_company": "Isthmus Edge Management", "is_synthetic": 1})
    quality[DEMO_OWNER_ID] = (2.0, True)

    # ---------------- properties
    hoods = list(NEIGHBORHOODS)
    hood_w = [NEIGHBORHOODS[h][2] for h in hoods]
    owner_ids = [o["owner_id"] for o in owners if o["owner_id"] != DEMO_OWNER_ID]
    # Skewed ownership: some owners hold many buildings.
    owner_w = [rng.paretovariate(1.3) for _ in owner_ids]
    properties = []
    seen_addr = set()
    for i in range(n_properties):
        h = rng.choices(hoods, weights=hood_w, k=1)[0]
        lat0, lon0, campus_w, streets = NEIGHBORHOODS[h]
        while True:
            addr = f"{rng.randint(1, 29) * 100 + rng.randint(0, 99)} {rng.choice(streets)}"
            if addr not in seen_addr:
                seen_addr.add(addr)
                break
        units = rng.choice([1, 2, 2, 3, 4, 4, 6, 8, 12, 16, 24, 40])
        properties.append({
            "property_id": f"P-{i:05d}", "address_norm": addr,
            "lat": round(lat0 + rng.gauss(0, 0.0035), 6), "lon": round(lon0 + rng.gauss(0, 0.0045), 6),
            "neighborhood": h, "units": units, "year_built": rng.randint(1890, 2020),
            "owner_id": rng.choices(owner_ids, weights=owner_w, k=1)[0], "is_synthetic": 1,
        })

    # Demo owner: demo building + 3 others
    demo_props = [
        {"property_id": DEMO_PROPERTY_ID, "address_norm": DEMO_ADDRESS, "lat": 43.0759, "lon": -89.3978,
         "neighborhood": "Langdon", "units": 24, "year_built": 1924, "owner_id": DEMO_OWNER_ID, "is_synthetic": 1},
        {"property_id": "P-DEMO-A", "address_norm": "415 W MIFFLIN ST", "lat": 43.0717, "lon": -89.3920,
         "neighborhood": "Mifflin", "units": 16, "year_built": 1911, "owner_id": DEMO_OWNER_ID, "is_synthetic": 1},
        {"property_id": "P-DEMO-B", "address_norm": "1020 REGENT ST", "lat": 43.0683, "lon": -89.4098,
         "neighborhood": "Regent", "units": 12, "year_built": 1938, "owner_id": DEMO_OWNER_ID, "is_synthetic": 1},
        {"property_id": "P-DEMO-C", "address_norm": "222 N BASSETT ST", "lat": 43.0727, "lon": -89.3889,
         "neighborhood": "Mifflin", "units": 16, "year_built": 1905, "owner_id": DEMO_OWNER_ID, "is_synthetic": 1},
    ]
    properties.extend(demo_props)

    # ---------------- reports (historic)
    prop_w = []
    for p in properties:
        q, _ = quality[p["owner_id"]]
        age = max(0, 2025 - p["year_built"])
        prop_w.append(p["units"] ** 0.8 * q * (1 + age / 120))
    reports = []
    days = (now - start).days
    for i in range(n_reports):
        p = rng.choices(properties, weights=prop_w, k=1)[0]
        if p["owner_id"] == DEMO_OWNER_ID:
            continue  # demo owner's history is hand-crafted below
        # rejection-sample a date by seasonality
        while True:
            d = start + timedelta(days=rng.randrange(days), hours=rng.randrange(24))
            t = _pick_type(rng, d.month)
            if rng.random() < min(1.0, _season_weight(t, d.month) / 2.5 + 0.35):
                break
        reports.append(_mk_report(rng, f"R-{i:06d}", p, t, d, now, quality))

    # The hand-crafted demo story gets its own random stream, so tuning the background data can never move it.
    reports.extend(_demo_reports(random.Random(f"fixit-demo-story-{seed}"), now, quality))
    return {"owners": owners, "properties": properties, "reports": reports}


def _mk_report(rng, rid, p, t, d, now, quality, force_open=False):
    q, bad = quality[p["owner_id"]]
    sev = _severity(t, d.month)
    base = {"emergency": 3, "urgent": 10, "routine": 25}[sev]
    days_to_fix = rng.lognormvariate(math.log(base * (2.6 if bad else 1.0)), 0.6)
    fixed_at = d + timedelta(days=days_to_fix)
    p_never = 0.12 if bad else 0.03
    if force_open or fixed_at > now or rng.random() < p_never:
        status = "escalated" if (now - d).days > 30 and rng.random() < 0.4 else "open"
        fixed = None
    else:
        status, fixed = "fixed", fixed_at.isoformat(timespec="seconds")
    unit = str(rng.randint(1, max(1, p["units"])))
    return {
        "report_id": rid, "property_id": p["property_id"], "unit_hash": unit_hash(p["property_id"], unit),
        "violation_category": CATEGORY_OF[t], "violation_type": t, "severity": sev,
        "reported_at": d.isoformat(timespec="seconds"), "fixed_at": fixed, "status": status, "source": "synthetic",
    }


def _demo_reports(rng, now, quality):
    out = []
    demo_b = {"property_id": DEMO_PROPERTY_ID, "owner_id": DEMO_OWNER_ID, "units": 24}
    # 6 recent HEAT reports in the demo building (units 2..7), last 7 days, all open.
    for k in range(6):
        d = now - timedelta(days=rng.uniform(0.5, 6.5))
        r = _mk_report(rng, f"R-DEMO-HEAT-{k}", demo_b, "NO_HEAT", d, now, quality, force_open=True)
        r["unit_hash"] = unit_hash(DEMO_PROPERTY_ID, str(k + 2))
        r["status"] = "open"
        out.append(r)
    # Older, slowly fixed history at the demo building (gives the timeline + D grade).
    hist = ["WATER_DAMAGE_MOLD", "PEST_EVIDENCE", "NO_HEAT", "LEAK_PLUMBING", "DAMAGED_SURFACES", "NO_HEAT",
            "BROKEN_LOCK", "WATER_DAMAGE_MOLD"]
    for k, t in enumerate(hist):
        d = now - timedelta(days=60 + k * 95 + rng.randint(0, 30))
        r = _mk_report(rng, f"R-DEMO-H-{k}", demo_b, t, d, now, quality)
        if r["status"] != "fixed":
            r["status"], r["fixed_at"] = "fixed", (d + timedelta(days=rng.randint(12, 40))).isoformat(timespec="seconds")
        out.append(r)
    # 11 open issues across the other 3 buildings (4 + 4 + 3).
    plan = {"P-DEMO-A": ["WATER_DAMAGE_MOLD", "PEST_EVIDENCE", "NO_HEAT", "LEAK_PLUMBING"],
            "P-DEMO-B": ["NO_HEAT", "BROKEN_LOCK", "WATER_DAMAGE_MOLD", "DAMAGED_SURFACES"],
            "P-DEMO-C": ["EXPOSED_WIRING", "NO_HEAT", "PEST_EVIDENCE"]}
    units = {"P-DEMO-A": 16, "P-DEMO-B": 12, "P-DEMO-C": 16}
    for pid, types in plan.items():
        b = {"property_id": pid, "owner_id": DEMO_OWNER_ID, "units": units[pid]}
        for k, t in enumerate(types):
            d = now - timedelta(days=rng.uniform(3, 45))
            r = _mk_report(rng, f"R-DEMO-{pid[-1]}-{k}", b, t, d, now, quality, force_open=True)
            r["status"] = "open"
            out.append(r)
        # a little fixed history too
        for k in range(3):
            d = now - timedelta(days=120 + k * 140)
            r = _mk_report(rng, f"R-DEMO-{pid[-1]}-H{k}", b, rng.choice(list(TYPE_WEIGHTS)), d, now, quality)
            if r["status"] != "fixed":
                r["status"], r["fixed_at"] = "fixed", (d + timedelta(days=rng.randint(10, 35))).isoformat(timespec="seconds")
            out.append(r)
    return out
