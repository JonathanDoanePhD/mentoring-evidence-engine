"""Compare screening decisions from two runs of the same batches (e.g. reference model vs a
cheaper model) to decide whether the cheaper model is good enough for screening.

python3 -I scripts/calibration.py screen screen_calibration_sonnet -> output/screening_calibration.csv
Reports agreement on the decision that matters downstream (include_outcome/include_review vs
everything else) and on the full 6-way decision, with Cohen's kappa and the disagreements.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "coded"
ref_dir, alt_dir = sys.argv[1], sys.argv[2]
INCLUDE = {"include_outcome", "include_review"}


def load(d):
    return pd.DataFrame([e for f in sorted((C / d).glob("batch_*.json")) for e in json.loads(f.read_text())])


alt = load(alt_dir)
ref = load(ref_dir)
m = ref.merge(alt, on="id", suffixes=("_ref", "_alt"))


def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in np.union1d(a, b))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


m["inc_ref"] = m.decision_ref.isin(INCLUDE)
m["inc_alt"] = m.decision_alt.isin(INCLUDE)
res = pd.DataFrame([
    {"comparison": "include (outcome/review) vs not", "n": len(m), "agree": (m.inc_ref == m.inc_alt).mean(), "kappa": kappa(m.inc_ref, m.inc_alt),
     "ref_includes": int(m.inc_ref.sum()), "alt_includes": int(m.inc_alt.sum()),
     "alt_recall_of_ref_includes": (m.inc_alt & m.inc_ref).sum() / max(m.inc_ref.sum(), 1),
     "alt_precision": (m.inc_alt & m.inc_ref).sum() / max(m.inc_alt.sum(), 1)},
    {"comparison": "full 6-way decision", "n": len(m), "agree": (m.decision_ref == m.decision_alt).mean(),
     "kappa": kappa(m.decision_ref, m.decision_alt)},
])
res.to_csv(ROOT / "output" / "screening_calibration.csv", index=False, float_format="%.3f")
print(res.round(3).to_string(index=False))
dis = m[m.inc_ref != m.inc_alt][["id", "decision_ref", "decision_alt", "reason_ref", "reason_alt"]]
print(f"\nInclude/exclude disagreements ({len(dis)}):")
print(dis.to_string(index=False, max_colwidth=60))
