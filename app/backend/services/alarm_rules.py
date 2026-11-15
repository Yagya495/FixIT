"""Smoke / CO alarm source applicability: a limited, NONPERSISTENT prototype (pure logic, no I/O).

Given building facts the TENANT entered (never photos, never the synthetic demo-building records), list which legal
sources might be relevant and why. Rules, set by the user on 2026-11-14:
  - Keep MGO 34.907, the Wisconsin smoke statutes, the Wisconsin CO statutes and the SPS references SEPARATE.
  - Never choose a governing rule.
  - Never assert that a source definitely applies when its scope or exceptions are unresolved. The strongest status
    is "conditions_met_unverified": every stated condition FixIt read is answered and met, nothing unresolved is
    known, and it is still NOT legally verified.
  - The five-day written-notice deadline display stays DISABLED until its applicability and written-notice
    requirements are verified and individually approved. Nothing here computes or returns a deadline.
Sources and quotes: docs/legal/OTHER_SOURCES_REVIEW.md (sections 2, 5 and 6).
"""
from __future__ import annotations

# Hard-coded off on purpose (not an env var): turning it on requires a reviewed code change.
LEGAL_DEADLINE_DISPLAY_ENABLED = False
DEADLINE_DISABLED_REASON = ("A legal repair deadline is not shown yet. FixIt is still verifying when it applies and what "
                            "written notice is required.")

UNITS = ("1", "2", "3+", "unknown")
BUILT = ("before_1980_06_01", "1980_06_01_to_2008", "2009_or_later", "unknown")
YNU = ("yes", "no", "unknown")
FIELDS = {"units": UNITS, "built": BUILT, "owner_occupied": YNU, "attached_garage": YNU, "fireplace": YNU,
          "fuel_burning_appliance": YNU, "fuel_forced_air_furnace": YNU}
LABELS = {"units": "number of residential units", "built": "construction period",
          "owner_occupied": "whether the owner lives in the building", "attached_garage": "attached garage",
          "fireplace": "fireplace", "fuel_burning_appliance": "fuel-burning appliance",
          "fuel_forced_air_furnace": "fuel-burning forced-air furnace"}

CONDITIONS_MET = "conditions_met_unverified"   # stated conditions answered and met; NOT legal verification
MAY_APPLY = "may_apply"                        # facts missing, or scope/exceptions unresolved
OUT_OF_SCOPE = "outside_stated_scope"          # the source's own text excludes this building
NOT_EVALUATED = "not_evaluated"                # FixIt cannot assess it from these facts
STATUS_TEXT = {
    CONDITIONS_MET: "Stated conditions appear met (not legally verified)",
    MAY_APPLY: "May apply",
    OUT_OF_SCOPE: "Outside the source's stated scope",
    NOT_EVALUATED: "Not evaluated",
}


# Wis. Stat. 101.01(12) (read 2026-11-14): "public building" includes a structure used "by 3 or more tenants".
# FixIt asks about units, not tenants, so this is reported, never evaluated.
PUBLIC_BUILDING_NOTE = ("Wis. Stat. 101.01(12) counts a building used by 3 or more tenants as a 'public building'; "
                        "FixIt asks about units, not tenants, so this is not evaluated.")


def normalize(profile: dict | None) -> dict:
    """Every field defaults to 'unknown'; anything not in the allowed values also becomes 'unknown'."""
    p = profile or {}
    return {k: (p.get(k) if p.get(k) in allowed else "unknown") for k, allowed in FIELDS.items()}


def _src(sid, title, kind, status, reasons, missing=(), unresolved=()):
    return {"source_id": sid, "title": title, "kind": kind, "status": status, "status_text": STATUS_TEXT[status],
            "reasons": list(reasons), "missing": [LABELS[m] for m in missing], "unresolved": list(unresolved),
            "verified": False}


def _one_or_two(u):
    return u in ("1", "2")


def smoke_sources(p: dict) -> list[dict]:
    u, b, occ = p["units"], p["built"], p["owner_occupied"]
    out = []

    # MGO 34.907 (Madison): buildings built before 2009; owner-occupied single-family homes excluded from (1)(b).
    mgo_unres = ["Exception (1)(e) (detectors already installed under other codes) is not evaluated.",
                 "Internal references 'sub. (2)(a)/(2)(b)/(3)(h)' don't match the current numbering."]
    if b == "2009_or_later":
        out.append(_src("MGO 34.907", "Madison smoke alarm ordinance", "Madison ordinance", OUT_OF_SCOPE,
                        ["Applies to buildings built before 2009; later buildings follow IFC section 907 (not reviewed)."]))
    elif u == "1" and occ == "yes":
        out.append(_src("MGO 34.907", "Madison smoke alarm ordinance", "Madison ordinance", OUT_OF_SCOPE,
                        ["Subsection (1)(b) excludes owner-occupied single family homes."], unresolved=mgo_unres[:1]))
    else:
        missing = [m for m, v in (("built", b), ("units", u)) if v == "unknown"]
        if u == "1" and occ == "unknown":
            missing.append("owner_occupied")
        out.append(_src("MGO 34.907", "Madison smoke alarm ordinance", "Madison ordinance", MAY_APPLY,
                        ["Covers residential buildings built before 2009 (single family homes, duplexes, apartments…)."],
                        missing, mgo_unres))

    # Wis. Stat. 101.645: dwellings (1 or 2 dwelling units, 101.61(1)).
    if u == "3+":
        out.append(_src("Wis. Stat. 101.645", "State smoke detectors: dwellings", "Wisconsin statute", OUT_OF_SCOPE,
                        ["'Dwelling' means a building with 1 or 2 dwelling units (101.61(1))."]))
    elif _one_or_two(u):
        out.append(_src("Wis. Stat. 101.645", "State smoke detectors: dwellings", "Wisconsin statute", CONDITIONS_MET,
                        ["Building has 1 or 2 units, the statute's stated scope."]))
    else:
        out.append(_src("Wis. Stat. 101.645", "State smoke detectors: dwellings", "Wisconsin statute", MAY_APPLY,
                        ["Covers buildings with 1 or 2 dwelling units."], ["units"]))

    # Wis. Stat. 101.145: "residential building" = public building used for sleeping or lodging (scope unresolved).
    pub = [PUBLIC_BUILDING_NOTE]
    if u == "3+" or u == "unknown":
        out.append(_src("Wis. Stat. 101.145", "State smoke detectors: residential buildings", "Wisconsin statute",
                        MAY_APPLY, ["Covers public buildings used for sleeping or lodging, incl. apartment houses."],
                        ["units"] if u == "unknown" else [], pub))
    else:
        out.append(_src("Wis. Stat. 101.145", "State smoke detectors: residential buildings", "Wisconsin statute",
                        NOT_EVALUATED, ["A 1-2 unit building may still be a 'public building' if 3 or more tenants use it (Wis. Stat. 101.01(12)); FixIt does not evaluate this."],
                        unresolved=pub))

    out.append(_sps328(p, "smoke"))
    return out


def co_sources(p: dict) -> list[dict]:
    u = p["units"]
    g, f, a, fa = p["attached_garage"], p["fireplace"], p["fuel_burning_appliance"], p["fuel_forced_air_furnace"]
    out = []

    # Wis. Stat. 101.647: dwellings; not required with no attached garage, no fireplace AND no fuel-burning appliance.
    if u == "3+":
        out.append(_src("Wis. Stat. 101.647", "State CO detectors: dwellings", "Wisconsin statute", OUT_OF_SCOPE,
                        ["'Dwelling' means a building with 1 or 2 dwelling units (101.61(1))."]))
    elif _one_or_two(u) and "yes" in (g, f, a):
        out.append(_src("Wis. Stat. 101.647", "State CO detectors: dwellings", "Wisconsin statute", CONDITIONS_MET,
                        ["1-2 unit building with an attached garage, fireplace or fuel-burning appliance."]))
    elif _one_or_two(u) and (g, f, a) == ("no", "no", "no"):
        out.append(_src("Wis. Stat. 101.647", "State CO detectors: dwellings", "Wisconsin statute", OUT_OF_SCOPE,
                        ["Stated exemption: no attached garage, no fireplace and no fuel-burning appliance."]))
    else:
        missing = (["units"] if u == "unknown" else []) + [m for m, v in (("attached_garage", g), ("fireplace", f),
                                                                           ("fuel_burning_appliance", a)) if v == "unknown"]
        out.append(_src("Wis. Stat. 101.647", "State CO detectors: dwellings", "Wisconsin statute", MAY_APPLY,
                        ["Covers 1-2 unit buildings unless there is no attached garage, fireplace or fuel-burning appliance."],
                        missing))

    # Wis. Stat. 101.149: residential buildings; triggers each have exemptions that FixIt doesn't evaluate.
    exempt = ["Trigger-specific exemptions in 101.149(2) and the sealed-combustion exception in 101.149(5) are not evaluated.",
              "The 'fuel-burning appliances outside the unit' trigger is not asked.",
              PUBLIC_BUILDING_NOTE]
    if u in ("3+", "unknown"):
        missing = (["units"] if u == "unknown" else []) + [m for m, v in (("fuel_burning_appliance", a),
                                                                           ("fuel_forced_air_furnace", fa),
                                                                           ("attached_garage", g)) if v == "unknown"]
        out.append(_src("Wis. Stat. 101.149", "State CO detectors: residential buildings", "Wisconsin statute",
                        MAY_APPLY, ["Triggered by a fuel-burning appliance, a fuel-burning forced-air furnace, "
                                    "fuel-burning appliances outside the unit, or an attached garage."], missing, exempt))
    else:
        out.append(_src("Wis. Stat. 101.149", "State CO detectors: residential buildings", "Wisconsin statute",
                        NOT_EVALUATED, ["A 1-2 unit building may still be a 'public building' if 3 or more tenants use it (Wis. Stat. 101.01(12)); FixIt does not evaluate this."],
                        unresolved=exempt[2:]))

    out.append(_sps328(p, "co"))
    return out


def _sps328(p: dict, kind: str) -> dict:
    """Wis. Admin. Code ch. SPS 328 (adopted by MGO 29.22): 1-2 family dwellings, construction before June 1, 1980."""
    u, b = p["units"], p["built"]
    title = "SPS 328 (via MGO 29.22): existing 1-2 family dwellings"
    co_exempt = kind == "co" and (p["attached_garage"], p["fireplace"], p["fuel_burning_appliance"]) == ("no", "no", "no")
    if u == "3+" or b in ("1980_06_01_to_2008", "2009_or_later"):
        return _src("SPS 328", title, "Wisconsin administrative code", OUT_OF_SCOPE,
                    ["Applies to one- and 2-family dwellings whose construction began before June 1, 1980."])
    if _one_or_two(u) and b == "before_1980_06_01":
        if co_exempt:
            return _src("SPS 328", title, "Wisconsin administrative code", OUT_OF_SCOPE,
                        ["SPS 328 doesn't require a CO detector where the 101.647(3)(a) exemption applies."])
        if kind == "co" and "unknown" in (p["attached_garage"], p["fireplace"], p["fuel_burning_appliance"]):
            return _src("SPS 328", title, "Wisconsin administrative code", MAY_APPLY,
                        ["1-2 family dwelling built before June 1, 1980; the 101.647(3)(a) exemption can't be ruled out."],
                        [m for m in ("attached_garage", "fireplace", "fuel_burning_appliance") if p[m] == "unknown"])
        return _src("SPS 328", title, "Wisconsin administrative code", CONDITIONS_MET,
                    ["1-2 family dwelling built before June 1, 1980."])
    missing = [m for m, v in (("units", u), ("built", b)) if v == "unknown"]
    return _src("SPS 328", title, "Wisconsin administrative code", MAY_APPLY,
                ["Applies to one- and 2-family dwellings whose construction began before June 1, 1980."], missing)


def evaluate(profile: dict | None, alarm_types: list[str] | tuple[str, ...] = ("smoke", "co")) -> dict:
    """Pure function. Uses ONLY the tenant-entered profile; nothing is stored."""
    p = normalize(profile)
    result = {"profile": p, "governing_rule": None,
              "governing_rule_note": "FixIt does not choose which rule governs when more than one may apply.",
              "deadline": {"enabled": LEGAL_DEADLINE_DISPLAY_ENABLED, "reason": DEADLINE_DISABLED_REASON},
              "notes": ["Not legal advice. These sources are not yet verified by FixIt's reviewer.",
                        "Answers are used only for this view and are not saved.",
                        "Madison's rent-abatement schedule cites '29.19' for CO detectors, but the current MGO 29.19 "
                        "is about accrediting standards: unresolved."],
              "alarms": {}}
    if "smoke" in alarm_types:
        result["alarms"]["smoke"] = smoke_sources(p)
    if "co" in alarm_types:
        result["alarms"]["co"] = co_sources(p)
    return result
