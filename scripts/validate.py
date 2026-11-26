"""Validate an agent's output file against the protocol. Exit code 0 = valid.

python3 -I scripts/validate.py screen data/coded/screen/batch_0001.json
python3 -I scripts/validate.py code   data/coded/code/<coder>/batch_0001.json
python3 -I scripts/validate.py adjudicate data/coded/adjudicate/batch_0001.json
Checks: valid JSON list, one entry per record in the matching input batch (no missing,
extra or duplicate IDs), allowed values only, short free-text fields.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = {"include_outcome", "include_review", "include_other", "exclude_adult", "exclude_not_mentoring", "exclude_other"}
POPS = {"k12_elementary", "k12_middle", "k12_high", "k12_mixed", "college_undergrad", "out_of_school_youth", "youth_other", "adult", "unclear"}
CONF = {"high", "medium", "low"}
ENUMS = {
    "design": {"rct", "quasi_experimental", "pre_post", "correlational", "review", "other"},
    "country": None,
    "setting": {"school_based", "community_based", "online", "workplace_career", "college_campus", "mixed", "unclear"},
    "format": {"one_to_one", "group", "peer_cross_age", "mixed", "natural_mentor", "unclear"},
    "mentor_type": {"adult_volunteer", "paid_staff", "college_student", "older_peer", "teacher_school_staff", "natural_informal", "mixed", "unclear"},
    "grade_band": {"elementary", "middle", "high", "k12_mixed", "college", "out_of_school", "unclear"},
    "frequency": {"weekly_or_more", "biweekly", "monthly", "other", "not_reported"},
    "bridging": {"yes", "no", "unclear"},
}
TARGETS = {"low_income", "racial_ethnic_minority", "at_risk_behavior", "juvenile_justice", "foster_care", "first_generation",
           "disability", "girls_women_stem", "stem_general", "lgbtq", "gifted", "immigrant_ell", "rural", "urban", "general"}
DOMAINS = {"academic_achievement", "engagement_attendance", "graduation_persistence", "college_access_enrollment",
           "self_efficacy_confidence", "belonging_connectedness", "psychosocial_other", "behavior_delinquency",
           "mental_health", "career_employment", "relationships_social"}
DIRS = {"positive", "null", "negative", "mixed"}
METRICS = {"d", "g", "or", "r", "pct_points", "other"}


def words(s):
    return len(str(s or "").split())


def batch_ids(kind, path):
    name = Path(path).stem  # batch_NNNN
    sub = "screen" if kind == "screen" else "code"
    f = ROOT / "data" / "interim" / "batches" / sub / f"{name}.jsonl"
    if kind == "adjudicate":
        f = ROOT / "data" / "interim" / "batches" / "adjudicate" / f"{name}.jsonl"
    return [json.loads(l)["id"] for l in open(f)]


def check_code(e, errs, i):
    for k, allowed in ENUMS.items():
        if k not in e:
            errs.append(f"[{i}] missing {k}")
        elif allowed and e[k] not in allowed:
            errs.append(f"[{i}] bad {k}={e[k]!r}")
    if not isinstance(e.get("rigor"), int) or not 1 <= e["rigor"] <= 5:
        errs.append(f"[{i}] rigor must be int 1-5")
    if e.get("n_youth") is not None and not isinstance(e["n_youth"], int):
        errs.append(f"[{i}] n_youth must be int or null")
    if e.get("duration_months") is not None and not isinstance(e["duration_months"], (int, float)):
        errs.append(f"[{i}] duration_months must be number or null")
    if not isinstance(e.get("targets"), list) or any(t not in TARGETS for t in e["targets"]):
        errs.append(f"[{i}] bad targets")
    if not isinstance(e.get("outcomes"), dict) or any(k not in DOMAINS or v not in DIRS for k, v in e["outcomes"].items()):
        errs.append(f"[{i}] bad outcomes")
    if not isinstance(e.get("effect_sizes"), list):
        errs.append(f"[{i}] effect_sizes must be a list")
    else:
        for es in e["effect_sizes"]:
            if es.get("domain") not in DOMAINS or es.get("metric") not in METRICS or not isinstance(es.get("value"), (int, float)):
                errs.append(f"[{i}] bad effect size {es}")
    rd = e.get("review_details")
    if e.get("design") == "review" and not isinstance(rd, dict):
        errs.append(f"[{i}] review_details required for reviews")
    if words(e.get("notes")) > 25:
        errs.append(f"[{i}] notes too long")


STOPW = set("the a an of and or for in on to with by from at as is are was were be this that these those not no "
             "study program programs students student youth mentoring mentor mentors mentees mentee school "
             "outcomes outcome effects effect research based about among into using use used".split())


def alignment(path, kind="screen"):
    """Share of records whose reason overlaps its own record more than its neighbours (shift check)."""
    import re
    w = lambda t: {x for x in re.findall(r"[a-z]{4,}", str(t).lower()) if x not in STOPW}
    out = {e["id"]: e for e in json.loads(Path(path).read_text())}
    sub = {"screen": "screen", "code": "code", "adjudicate": "adjudicate"}[kind]
    field = "reason" if kind == "screen" else "notes"
    f = ROOT / "data" / "interim" / "batches" / sub / f"{Path(path).stem}.jsonl"
    inp = [json.loads(l) for l in open(f)]
    tx = [w(r["title"] + " " + (r.get("abstract") or "")) for r in inp]
    wins = n = 0
    for i, r in enumerate(inp):
        rw = w(out.get(r["id"], {}).get(field, ""))
        if len(rw) < 2:
            continue
        own = len(rw & tx[i]); nb = max(len(rw & tx[j]) for j in (i - 1, i + 1) if 0 <= j < len(inp))
        n += 1; wins += 1 if own > nb else (0.5 if own == nb and own > 0 else 0)
    return wins / n if n else 1.0


def main(kind, path):
    errs = []
    try:
        data = json.loads(Path(path).read_text())
    except Exception as ex:
        print(f"INVALID JSON: {ex}"); return 1
    if not isinstance(data, list):
        print("INVALID: top level must be a list"); return 1
    expected = batch_ids(kind, path)
    got = [e.get("id") for e in data]
    if sorted(got) != sorted(expected):
        missing, extra = set(expected) - set(got), set(got) - set(expected)
        errs.append(f"id mismatch: missing {sorted(missing)[:5]} ({len(missing)}), extra {sorted(extra)[:5]} ({len(extra)}), dupes {len(got) - len(set(got))}")
    for i, e in enumerate(data):
        if kind == "screen":
            if e.get("decision") not in DECISIONS: errs.append(f"[{i}] bad decision {e.get('decision')!r}")
            if e.get("population") not in POPS: errs.append(f"[{i}] bad population {e.get('population')!r}")
            if e.get("confidence") not in CONF: errs.append(f"[{i}] bad confidence")
            if words(e.get("reason")) > 20: errs.append(f"[{i}] reason too long")
        else:
            check_code(e, errs, i)
    if not errs:
        a = alignment(path, kind)
        if a < 0.75:
            errs.append(f"reasons do not match their records (alignment {a:.2f} < 0.75): decisions look shifted. "
                        "Rebuild the file by matching each record's id to its own text.")
    if errs:
        print("INVALID:\n" + "\n".join(errs[:40]))
        return 1
    print(f"VALID: {len(data)} records")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
