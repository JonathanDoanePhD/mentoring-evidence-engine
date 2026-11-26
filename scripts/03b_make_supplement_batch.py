"""Stage 1 supplement (protocol v1.2): one extra batch of records outside the core stratum
that mention mentoring 3+ times in title + abstract and were not already sampled.

Why: the recall samples showed that relevant studies outside the core are mostly
multi-component programs where mentoring is one ingredient (mentioned once). The few that
are clearly ABOUT mentoring mention it repeatedly; this batch captures them cheaply.
Idempotent: rewrites batch_0062 and its manifest rows each run.

python3 -I scripts/03b_make_supplement_batch.py
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
C = ROOT / "data" / "coded"
BATCH = 62

r = pd.read_json(INTERIM / "candidates.jsonl", lines=True)
r = r[~r.tier.str.endswith("noabstract")]
man = pd.read_csv(C / "screen_manifest.csv")
man = man[man.batch != BATCH]
core = r.title.str.contains("mentor", case=False) | r.subjects.apply(lambda s: any(re.search("mentor", x, re.I) for x in s))
cnt = (r.title + " " + r.abstract).str.lower().str.count("mentor")
sup = r[~core & ~r.id.isin(man.id) & (cnt >= 3)].sort_values("id")
with open(INTERIM / "batches" / "screen" / f"batch_{BATCH:04d}.jsonl", "w") as f:
    for _, x in sup.iterrows():
        f.write(json.dumps({"id": x.id, "year": int(x.year) if pd.notna(x.year) else None, "title": x.title,
                            "abstract": x.abstract, "descriptors": x.subjects, "levels": x.levels, "types": x.types}) + "\n")
rows = pd.DataFrame({"batch": BATCH, "id": sup.id, "stratum": "supplement_mentor3plus",
                     "stratum_population": len(sup), "sampling_weight": 1.0, "year": sup.year, "peer_reviewed": sup.peer_reviewed})
pd.concat([man, rows]).to_csv(C / "screen_manifest.csv", index=False)
print(f"supplement batch {BATCH}: {len(sup)} records")
