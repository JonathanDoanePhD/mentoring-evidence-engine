"""Stage 1 setup: build screening batches (deterministic, so they can be rebuilt any time).

Selection: all Tier A "core" records (mentoring in title or descriptors) + fixed-seed random
recall-check samples: 400 Tier A peripheral, 300 Tier B, 150 Tier X.
Batches of 150 records -> data/interim/batches/screen/batch_NNNN.jsonl (abstract text, not committed)
Manifest (ids + tier per batch) -> data/coded/screen_manifest.csv (committed)

python3 -I scripts/03_make_screen_batches.py
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
CODED = ROOT / "data" / "coded"
BATCH_DIR = INTERIM / "batches" / "screen"
for p in (CODED, BATCH_DIR):
    p.mkdir(parents=True, exist_ok=True)
SIZE = 150
SEED = 20261114

r = pd.read_json(INTERIM / "candidates.jsonl", lines=True)
r = r[~r.tier.str.endswith("noabstract")]
core = r.title.str.contains("mentor", case=False) | r.subjects.apply(lambda s: any(re.search("mentor", x, re.I) for x in s))
r["stratum"] = "other"
r.loc[(r.tier == "A") & core, "stratum"] = "A_core"
r.loc[(r.tier == "A") & ~core, "stratum"] = "A_peripheral"
r.loc[r.tier == "B", "stratum"] = "B"
r.loc[r.tier == "X", "stratum"] = "X"
pop = r.groupby("stratum").size()
sample_n = {"A_core": None, "A_peripheral": 400, "B": 300, "X": 150}
parts = []
for s, n in sample_n.items():
    g = r[r.stratum == s]
    parts.append(g if n is None else g.sample(n=min(n, len(g)), random_state=SEED))
sel = pd.concat(parts).sort_values(["year", "id"]).reset_index(drop=True)
# interleave strata across batches so every batch mixes tiers (keeps agents calibrated)
sel = sel.sample(frac=1, random_state=SEED).reset_index(drop=True)
sel["batch"] = sel.index // SIZE + 1
sel["stratum_population"] = sel.stratum.map(pop)
sel["sampling_weight"] = sel.stratum.map(lambda s: 1.0 if sample_n[s] is None else pop[s] / min(sample_n[s], pop[s]))

for b, g in sel.groupby("batch"):
    with open(BATCH_DIR / f"batch_{b:04d}.jsonl", "w") as f:
        for _, x in g.iterrows():
            f.write(json.dumps({"id": x.id, "year": int(x.year) if pd.notna(x.year) else None, "title": x.title,
                                "abstract": x.abstract, "descriptors": x.subjects, "levels": x.levels,
                                "types": x.types}) + "\n")
sel[["batch", "id", "stratum", "stratum_population", "sampling_weight", "year", "peer_reviewed"]].to_csv(
    CODED / "screen_manifest.csv", index=False)
print(f"{len(sel):,} records in {sel.batch.max()} batches; by stratum: {sel.stratum.value_counts().to_dict()}")
