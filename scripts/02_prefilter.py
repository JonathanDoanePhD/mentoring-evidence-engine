"""Stage 0b: rule-based tiers, so agents spend effort where relevant studies are likely.

Tier A  youth signal AND (evaluation signal OR research review)  -> every record screened by agents
Tier B  everything else not clearly about adult professionals    -> random sample screened to
        estimate how many relevant studies the rules miss (recall check)
Tier X  adult/professional mentoring with no youth signal (teachers, faculty, graduate students,
        nurses, employees)                                       -> small sample screened as a check

Writes data/interim/candidates.jsonl (with tier) and output/prefilter_counts.csv.
python3 -I scripts/02_prefilter.py
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

recs = pd.read_json(INTERIM / "mentor_records.jsonl", lines=True)
recs["year"] = pd.to_numeric(recs.year, errors="coerce")
txt = (recs.title + " " + recs.abstract).str.lower()
subj = recs.subjects.apply(lambda s: " | ".join(s).lower())
lev = recs.levels.apply(lambda s: " | ".join(s).lower())
typ = recs.types.apply(lambda s: " | ".join(s).lower())

YOUTH_LEVELS = r"elementary|secondary|high school|middle school|junior high|grade \d|kindergarten|early childhood|primary education|k-12|intermediate grades"
YOUTH_WORDS = (r"\byouth|adolescen|teen|\bchild|children|juvenile|at[- ]risk (students|youth)|high school students|"
               r"middle school students|elementary school students|secondary school students|big brothers|big sisters|"
               r"boys and girls|foster (care|youth)|young people|students in grades|grade \d|\bk-12|first[- ]generation|"
               r"low[- ]income students|college access|dropout")
EVAL_WORDS = (r"effect|impact|outcome|evaluat|randomi[sz]|experiment|quasi|comparison group|control group|"
              r"matched|propensity|significant|pre[- ]?test|post[- ]?test|longitudinal|follow[- ]up|meta-analy")
REVIEW = r"meta-analy|systematic review|research review|literature review|research synthesis"
ADULT = (r"beginning teacher|new teacher|novice teacher|teacher induction|preservice|student teach|faculty|"
         r"doctoral|graduate student|nurs|physician|medical|residen(cy|ts)|employee|leadership development|"
         r"principal|administrator|librarian|counselor education|teacher educat|professional development")

youth = lev.str.contains(YOUTH_LEVELS) | txt.str.contains(YOUTH_WORDS) | subj.str.contains(YOUTH_WORDS)
evals = txt.str.contains(EVAL_WORDS) | typ.str.contains("reports - research|reports - evaluative")
review = txt.str.contains(REVIEW) | typ.str.contains("information analyses")
adult = (txt.str.contains(ADULT) | subj.str.contains(ADULT)) & ~youth
has_abstract = recs.abstract.str.len() >= 200

recs["tier"] = "B"
recs.loc[youth & (evals | review), "tier"] = "A"
recs.loc[adult, "tier"] = "X"
recs.loc[~has_abstract, "tier"] = recs.loc[~has_abstract, "tier"] + "-noabstract"
recs["review_flag"] = review

counts = recs.groupby("tier").size().rename("records").reset_index()
counts.to_csv(OUT / "prefilter_counts.csv", index=False)
recs.to_json(INTERIM / "candidates.jsonl", orient="records", lines=True)
print(counts.to_string(index=False))
a = recs[recs.tier == "A"]
print("Tier A by decade:", a.groupby((a.year // 10) * 10).size().to_dict())
print("Tier A peer reviewed share:", round(a.peer_reviewed.mean(), 2), "| median abstract chars:", int(a.abstract.str.len().median()))
