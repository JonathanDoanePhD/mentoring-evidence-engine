"""Detect misaligned screening files (decisions attached to the wrong records).

For each record, compare the content words of the agent's "reason" with the record's own
title + abstract vs. those of the records just before and after it. In an aligned file the
own-record overlap wins for most records; in a shifted file it wins only by chance.

python3 -I scripts/check_alignment.py [screen_dir]   -> output/screening_alignment.csv
Batches scoring below 0.6 are flagged for re-screening.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = sys.argv[1] if len(sys.argv) > 1 else "screen"
STOP = set("the a an of and or for in on to with by from at as is are was were be this that these those not no "
           "study program programs students student youth mentoring mentor mentors mentees mentee school "
           "outcomes outcome effects effect research based about among into using use used".split())
words = lambda s: {w for w in re.findall(r"[a-z]{4,}", str(s).lower()) if w not in STOP}

rows = []
for f in sorted((ROOT / "data" / "coded" / d).glob("batch_*.json")):
    out = {e["id"]: e for e in json.loads(f.read_text())}
    inp = [json.loads(l) for l in open(ROOT / "data" / "interim" / "batches" / "screen" / f"{f.stem}.jsonl")]
    texts = [words(r["title"] + " " + (r["abstract"] or "")) for r in inp]
    wins = n = 0
    for i, r in enumerate(inp):
        rw = words(out.get(r["id"], {}).get("reason", ""))
        if len(rw) < 2:
            continue
        own = len(rw & texts[i])
        nb = max(len(rw & texts[j]) for j in (i - 1, i + 1) if 0 <= j < len(inp))
        n += 1
        wins += own > nb or (own == nb and own > 0) * 0.5
    rows.append({"batch": f.stem, "scored": n, "alignment": wins / n if n else None})
res = pd.DataFrame(rows)
res["flag"] = res.alignment < 0.6
res.to_csv(ROOT / "output" / "screening_alignment.csv", index=False, float_format="%.3f")
print(res.sort_values("alignment").head(10).round(3).to_string(index=False))
print(f"flagged: {res.flag.sum()} of {len(res)} -> {res[res.flag].batch.tolist()}")
