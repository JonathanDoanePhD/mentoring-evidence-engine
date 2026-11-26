"""Stage 2 reconcile: compare coder A vs coder B, report reliability, send disagreements to
adjudication, and (once adjudication exists) write the final coded dataset.

Key fields adjudicated when coders disagree: design; rigor (if they differ by more than 1);
outcome directions; effect sizes. Other fields: agreed values kept; disagreements resolved
to "unclear"/null (or the adjudicator's value when one exists for that record).

python3 -I scripts/05_reconcile.py
  -> output/coding_reliability.csv
  -> data/interim/batches/adjudicate/batch_NNNN.jsonl (records needing adjudication + both codings)
  -> data/coded/final_coded.json (when every needed adjudication is present)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "coded"
INTERIM = ROOT / "data" / "interim"
ADJ_IN = INTERIM / "batches" / "adjudicate"
ADJ_IN.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "output"
CAT = ["design", "setting", "format", "mentor_type", "grade_band", "frequency", "bridging", "country"]
SIZE = 20


def load(coder):
    return {e["id"]: e for f in sorted((C / "code" / coder).glob("batch_*.json")) for e in json.loads(f.read_text())}


def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = (a == b).mean()
    cats = np.union1d(a, b)
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def es_key(e):
    return sorted((x["domain"], x["metric"], round(float(x["value"]), 2)) for x in e.get("effect_sizes", []))


A, B = load("coder_a"), load("coder_b")
ids = sorted(set(A) & set(B))
rel = []
for f in CAT:
    a = [str(A[i].get(f)) for i in ids]; b = [str(B[i].get(f)) for i in ids]
    rel.append({"field": f, "n": len(ids), "pct_agree": np.mean([x == y for x, y in zip(a, b)]), "kappa": kappa(a, b) if ids else np.nan})
ra = [A[i]["rigor"] for i in ids]; rb = [B[i]["rigor"] for i in ids]
rel.append({"field": "rigor (exact)", "n": len(ids), "pct_agree": np.mean([x == y for x, y in zip(ra, rb)]) if ids else np.nan,
            "kappa": kappa(ra, rb) if ids else np.nan})
rel.append({"field": "rigor (within 1)", "n": len(ids), "pct_agree": np.mean([abs(x - y) <= 1 for x, y in zip(ra, rb)]) if ids else np.nan, "kappa": np.nan})
doms = sorted({d for i in ids for d in list(A[i]["outcomes"]) + list(B[i]["outcomes"])})
for d in doms:
    a = [A[i]["outcomes"].get(d, "not_measured") for i in ids]; b = [B[i]["outcomes"].get(d, "not_measured") for i in ids]
    rel.append({"field": f"outcome:{d}", "n": len(ids), "pct_agree": np.mean([x == y for x, y in zip(a, b)]), "kappa": kappa(a, b)})
rel.append({"field": "effect_sizes (identical)", "n": len(ids), "pct_agree": np.mean([es_key(A[i]) == es_key(B[i]) for i in ids]) if ids else np.nan, "kappa": np.nan})
pd.DataFrame(rel).to_csv(OUT / "coding_reliability.csv", index=False, float_format="%.3f")


def needs_adj(i):
    a, b = A[i], B[i]
    return (a["design"] != b["design"] or abs(a["rigor"] - b["rigor"]) > 1 or a["outcomes"] != b["outcomes"]
            or es_key(a) != es_key(b))


need = [i for i in ids if needs_adj(i)]
code_recs, code_batch = {}, {}
for f in sorted((INTERIM / "batches" / "code").glob("batch_*.jsonl")):
    for l in open(f):
        r = json.loads(l); code_recs[r["id"]] = r; code_batch[r["id"]] = f.stem
# Adjudication batches mirror coding batches (adjudicate/batch_NNNN = disagreements from code
# batch NNNN) and are written only once BOTH coders have finished that batch, so their
# contents never change as more coding arrives and adjudication can start early.
done_a = {f.stem for f in (C / "code" / "coder_a").glob("batch_*.json")}
done_b = {f.stem for f in (C / "code" / "coder_b").glob("batch_*.json")}
by_batch = {}
for i in need:
    by_batch.setdefault(code_batch[i], []).append(i)
for b, lst in by_batch.items():
    if b in done_a and b in done_b:
        out = ADJ_IN / f"{b}.jsonl"
        if not out.exists():
            with open(out, "w") as fh:
                for i in sorted(lst):
                    fh.write(json.dumps({**code_recs[i], "coder_a": A[i], "coder_b": B[i]}) + "\n")

adj = {e["id"]: e for f in sorted((C / "adjudicate").glob("batch_*.json")) for e in json.loads(f.read_text())}
missing = [i for i in need if i not in adj]
print(f"Double-coded: {len(ids)} | need adjudication: {len(need)} | adjudicated: {len(need) - len(missing)}")
print(pd.DataFrame(rel).round(2).to_string(index=False))

if ids and not missing:
    final = []
    for i in ids:
        if i in adj:
            rec = dict(adj[i]); rec["resolution"] = "adjudicated"
        else:
            a, b = A[i], B[i]
            rec = {"id": i, "resolution": "agreed"}
            for f in CAT:
                rec[f] = a[f] if a.get(f) == b.get(f) else ("unclear" if f != "country" else "unclear")
            rec["rigor"] = round((a["rigor"] + b["rigor"]) / 2)
            rec["design"] = a["design"]
            rec["outcomes"] = a["outcomes"]
            rec["effect_sizes"] = a["effect_sizes"]
            rec["n_youth"] = a["n_youth"] if a.get("n_youth") == b.get("n_youth") else (a.get("n_youth") or b.get("n_youth"))
            rec["duration_months"] = a["duration_months"] if a.get("duration_months") == b.get("duration_months") else None
            rec["targets"] = sorted(set(a["targets"]) & set(b["targets"])) or sorted(set(a["targets"]) | set(b["targets"]))
            rec["program_name"] = a.get("program_name") or b.get("program_name")
            rec["review_details"] = a.get("review_details") or b.get("review_details")
            rec["notes"] = a.get("notes")
        final.append(rec)
    (C / "final_coded.json").write_text(json.dumps(final, indent=1))
    print(f"wrote data/coded/final_coded.json ({len(final)} records)")
