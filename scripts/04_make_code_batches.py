"""Stage 2 setup: batches of included studies for double coding.

Reads every validated screening file, keeps include_outcome + include_review, and writes
batches of 25 to data/interim/batches/code/ (deterministic order by id). Both coders get the
same batches. Run after screening is complete (refuses to run if screening is unfinished,
unless --partial is passed for a pilot).

python3 -I scripts/04_make_code_batches.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "coded"
INTERIM = ROOT / "data" / "interim"
OUT = INTERIM / "batches" / "code"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = 25

man = pd.read_csv(C / "screen_manifest.csv")
files = sorted((C / "screen").glob("batch_*.json"))
if len(files) < man.batch.nunique() and "--partial" not in sys.argv:
    sys.exit(f"Screening incomplete: {len(files)}/{man.batch.nunique()} batches. Use --partial for a pilot.")
import subprocess
ok = lambda f: subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "validate.py"), "screen", str(f)], capture_output=True).returncode == 0
files = [f for f in files if ok(f)]
if len(files) < man.batch.nunique() and "--partial" not in sys.argv:
    sys.exit(f"Screening incomplete or invalid: {len(files)}/{man.batch.nunique()} valid batches.")
scr = pd.DataFrame([e for f in files for e in json.loads(f.read_text())])
inc = scr[scr.decision.isin(["include_outcome", "include_review"])].merge(man[["id", "stratum"]], on="id")
# Scope (protocol v1.2): code only the fully screened, in-scope strata; recall-sample hits are
# used only to estimate what the scope leaves out.
inc = inc[inc.stratum.isin(["A_core", "supplement_mentor3plus"])].sort_values("id")
recs = pd.read_json(INTERIM / "candidates.jsonl", lines=True).set_index("id")
inc = inc[inc.id.isin(recs.index)].reset_index(drop=True)
inc["batch"] = inc.index // SIZE + 1
for old in OUT.glob("batch_*.jsonl"):
    old.unlink()
for b, g in inc.groupby("batch"):
    with open(OUT / f"batch_{b:04d}.jsonl", "w") as f:
        for _, x in g.iterrows():
            r = recs.loc[x.id]
            f.write(json.dumps({"id": x.id, "screen_decision": x.decision, "year": int(r.year) if pd.notna(r.year) else None,
                                "title": r.title, "abstract": r.abstract, "descriptors": r.subjects, "levels": r.levels,
                                "types": r.types, "peer_reviewed": bool(r.peer_reviewed), "source": r.source}) + "\n")
inc[["batch", "id", "decision", "population", "confidence"]].to_csv(C / "code_manifest.csv", index=False)
print(f"{len(inc):,} included records -> {inc.batch.max() if len(inc) else 0} code batches")
