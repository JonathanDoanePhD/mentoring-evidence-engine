"""Stage 3: report. Works on whatever is finished (screening only, or screening + coding).

Outputs in output/:
  screening_summary.csv     decisions by stratum, weighted estimates, recall of the rule-based tiers
  evidence_map.csv          coded studies by design x outcome domain: n studies, share positive
  study_features.csv        counts by design, rigor, decade, setting, format, mentor type, grade band, bridging
  effect_sizes.csv          every standardized effect size stated in an abstract
  effect_size_summary.csv   by domain: n, median, inverse-variance pooled d (where n is known)
  reviews.csv               reviews/meta-analyses with pooled effects
  graduation_college.csv    studies measuring graduation/persistence or college access
  priors.json               evidence-based ranges for Projects 03 and 07
  evidence_map.png, effect_sizes.png
python3 -I scripts/06_report.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "coded"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
INCLUDE = {"include_outcome", "include_review"}

# ---------------- Screening ----------------
man = pd.read_csv(C / "screen_manifest.csv")
import subprocess, sys
def _valid(f):
    return subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "validate.py"), "screen", str(f)], capture_output=True).returncode == 0
scr = pd.DataFrame([e for f in sorted((C / "screen").glob("batch_*.json")) if _valid(f) for e in json.loads(f.read_text())])
if scr.empty:
    raise SystemExit("No screening results yet: run the screening workflow first (see RESUME.md).")
s = man.merge(scr, on="id", how="inner")
s["relevant"] = s.decision.isin(INCLUDE)
summary = s.groupby("stratum").agg(screened=("id", "size"), population=("stratum_population", "first"),
                                   include_outcome=("decision", lambda d: (d == "include_outcome").sum()),
                                   include_review=("decision", lambda d: (d == "include_review").sum()),
                                   include_other=("decision", lambda d: (d == "include_other").sum()),
                                   relevant_rate=("relevant", "mean")).reset_index()
summary["est_relevant_in_population"] = summary.relevant_rate * summary.population
tot = summary.est_relevant_in_population.sum()
summary["share_of_all_relevant"] = summary.est_relevant_in_population / tot if tot else np.nan
summary.to_csv(OUT / "screening_summary.csv", index=False, float_format="%.3f")
core_share = summary.loc[summary.stratum == "A_core", "share_of_all_relevant"].sum()
in_scope_share = summary.loc[summary.stratum.isin(["A_core", "supplement_mentor3plus"]), "share_of_all_relevant"].sum()
decisions = s.decision.value_counts().to_dict()
print(f"Screened {len(s):,} of {len(man):,} records")
print(summary.round(3).to_string(index=False))
print(f"Estimated share of relevant records in the fully screened, in-scope set (core + supplement): {in_scope_share:.1%}")

# ---------------- Coding ----------------
final_path = C / "final_coded.json"
priors = {"screening": {"screened": int(len(s)), "decisions": {k: int(v) for k, v in decisions.items()},
                        "estimated_recall_A_core": round(float(core_share), 3), "estimated_in_scope_share": round(float(in_scope_share), 3)}}
if final_path.exists():
    f = pd.DataFrame(json.loads(final_path.read_text()))
    meta = man[["id", "year", "peer_reviewed"]]
    f = f.merge(meta, on="id", how="left")
    f["decade"] = (f.year // 10 * 10).astype("Int64")
    studies = f[f.design != "review"]
    reviews = f[f.design == "review"]

    feats = []
    for col in ["design", "rigor", "decade", "setting", "format", "mentor_type", "grade_band", "bridging", "country", "frequency"]:
        for k, v in studies[col].astype(str).value_counts().items():
            feats.append({"feature": col, "value": k, "n_studies": int(v), "share": v / len(studies)})
    tg = studies.explode("targets").targets.value_counts()
    for k, v in tg.items():
        feats.append({"feature": "targets", "value": k, "n_studies": int(v), "share": v / len(studies)})
    pd.DataFrame(feats).to_csv(OUT / "study_features.csv", index=False, float_format="%.3f")

    rows = []
    for _, r in studies.iterrows():
        for d, v in r.outcomes.items():
            rows.append({"id": r.id, "design": r.design, "rigor": r.rigor, "domain": d, "direction": v})
    o = pd.DataFrame(rows)
    em = o.groupby(["domain", "design"]).agg(n=("id", "nunique"), positive=("direction", lambda x: (x == "positive").mean()),
                                            null=("direction", lambda x: (x == "null").mean()),
                                            mixed=("direction", lambda x: (x == "mixed").mean()),
                                            negative=("direction", lambda x: (x == "negative").mean())).reset_index()
    em.to_csv(OUT / "evidence_map.csv", index=False, float_format="%.3f")

    # Rigor gradient: share of outcome findings that are positive, by rigor band (all domains and per domain)
    o["rigor_band"] = pd.cut(o.rigor, [0, 2, 3, 5], labels=["1-2", "3", "4-5"]).astype(str)
    agg = dict(n_findings=("id", "size"), n_studies=("id", "nunique"), positive=("direction", lambda x: (x == "positive").mean()),
               null=("direction", lambda x: (x == "null").mean()), mixed=("direction", lambda x: (x == "mixed").mean()),
               negative=("direction", lambda x: (x == "negative").mean()))
    pr = pd.concat([o.groupby("rigor_band").agg(**agg).reset_index().assign(domain="all"),
                    o.groupby(["domain", "rigor_band"]).agg(**agg).reset_index()])
    pr.to_csv(OUT / "positive_by_rigor.csv", index=False, float_format="%.3f")
    # Bridging programs vs others, within rigor band (to separate program type from study quality)
    ob = o.merge(studies[["id", "bridging"]], on="id")
    br = ob.groupby(["bridging", "rigor_band"]).agg(**agg).reset_index()
    br.to_csv(OUT / "bridging_by_rigor.csv", index=False, float_format="%.3f")
    priors["rigor_gradient_share_positive"] = {r.rigor_band: round(float(r.positive), 3) for r in pr[pr.domain == "all"].itertuples()}

    es = pd.DataFrame([{**e, "id": r.id, "design": r.design, "rigor": r.rigor, "n_youth": r.n_youth}
                       for _, r in f.iterrows() for e in (r.effect_sizes or [])])
    if len(es):
        es.to_csv(OUT / "effect_sizes.csv", index=False)
        std = es[es.metric.isin(["d", "g"]) & es.value.between(-3, 3) & (es.design != "review")].copy()
        out = []
        for dom, g in std.groupby("domain"):
            w = g.dropna(subset=["n_youth"]); w = w[w.n_youth > 10]
            var = 4 / w.n_youth + w.value ** 2 / (2 * w.n_youth)
            pooled = np.sum(w.value / var) / np.sum(1 / var) if len(w) else np.nan
            se = np.sqrt(1 / np.sum(1 / var)) if len(w) else np.nan
            # DerSimonian-Laird random effects
            if len(w) >= 3:
                q = np.sum((w.value - pooled) ** 2 / var); k = len(w)
                tau2 = max(0, (q - (k - 1)) / (np.sum(1 / var) - np.sum(1 / var ** 2) / np.sum(1 / var)))
                vr = var + tau2
                pooled_re = np.sum(w.value / vr) / np.sum(1 / vr); se_re = np.sqrt(1 / np.sum(1 / vr))
            else:
                pooled_re, se_re, tau2 = np.nan, np.nan, np.nan
            rct = g[g.design == "rct"]
            out.append({"domain": dom, "n_effects": len(g), "n_studies": g.id.nunique(), "median": g.value.median(),
                        "p25": g.value.quantile(.25), "p75": g.value.quantile(.75), "n_with_sample_size": len(w),
                        "pooled_re": pooled_re, "pooled_re_low": pooled_re - 1.96 * se_re, "pooled_re_high": pooled_re + 1.96 * se_re,
                        "tau2": tau2, "rct_median": rct.value.median() if len(rct) else np.nan, "rct_n": len(rct)})
        ess = pd.DataFrame(out)
        ess.to_csv(OUT / "effect_size_summary.csv", index=False, float_format="%.3f")
        priors["effect_sizes_from_abstracts"] = ess.round(3).replace({np.nan: None}).to_dict(orient="records")
    rv = reviews[["id", "year", "rigor", "outcomes", "review_details", "notes"]].copy()
    rv["n_studies"] = rv.review_details.apply(lambda x: (x or {}).get("n_studies"))
    rv["pooled_metric"] = rv.review_details.apply(lambda x: (x or {}).get("pooled_metric"))
    rv["pooled_value"] = rv.review_details.apply(lambda x: (x or {}).get("pooled_value"))
    rv.drop(columns="review_details").to_csv(OUT / "reviews.csv", index=False)
    pv = rv.dropna(subset=["pooled_value"])
    pv = pv[pv.pooled_metric.astype(str).str.lower().isin(["d", "g", "hedges g", "cohen's d", "smd", "standardized effect size"]) & pv.pooled_value.between(-2, 2)]
    priors["meta_analyses"] = {"n_reviews": int(len(rv)), "n_with_pooled_d_or_g": int(len(pv)),
                               "median_pooled": float(pv.pooled_value.median()) if len(pv) else None,
                               "range": [float(pv.pooled_value.min()), float(pv.pooled_value.max())] if len(pv) else None}
    if len(es):
        neg = es[(es.domain.isin(["graduation_persistence", "college_access_enrollment"])) & (es.metric == "pct_points") & (es.value < 0)]
        neg.to_csv(OUT / "review_negative_graduation_effects.csv", index=False)  # check sign convention (protocol v1.4)
        # Any domain: effect sign contradicts the coded outcome direction (likely sign-convention slips,
        # e.g. fewer absences recorded as negative). Listed for manual review, not auto-corrected.
        dirs = {(r.id, d): v for _, r in f.iterrows() for d, v in (r.outcomes or {}).items()}
        es["direction"] = [dirs.get((i, d)) for i, d in zip(es.id, es.domain)]
        es["resolution"] = es.id.map(f.set_index("id").resolution)
        es_eff = es[es.metric != "other"]
        conflict = es_eff[((es_eff.direction == "positive") & (es_eff.value < 0)) | ((es_eff.direction == "negative") & (es_eff.value > 0))]
        conflict.to_csv(OUT / "review_sign_conflicts.csv", index=False)
        priors["sign_conflicts_for_review"] = int(len(conflict))
    gc = o[o.domain.isin(["graduation_persistence", "college_access_enrollment"])]
    gcs = gc.merge(studies[["id", "year", "n_youth", "program_name", "grade_band", "setting"]], on="id")
    gcs.to_csv(OUT / "graduation_college.csv", index=False)
    grad = gc[gc.domain == "graduation_persistence"]
    priors["graduation"] = {
        "n_studies": int(grad.id.nunique()),
        "share_positive_all": float((grad.direction == "positive").mean()) if len(grad) else None,
        "share_positive_rigor_4plus": float((grad[grad.rigor >= 4].direction == "positive").mean()) if (grad.rigor >= 4).any() else None,
        "n_rigor_4plus": int((grad.rigor >= 4).sum()),
        "pct_point_effects": es[(es.domain == "graduation_persistence") & (es.metric == "pct_points")].value.tolist() if len(es) else [],
    }
    # Percentage-point effects by design: only randomized and comparison-group studies are usable as priors;
    # pre-post and comparisons with national/historical averages ("other") are listed but not pooled.
    if len(es):
        gp = es[(es.domain == "graduation_persistence") & (es.metric == "pct_points")]
        priors["graduation"]["pct_points_by_design"] = {
            d: {"n_effects": int(len(g)), "n_studies": int(g.id.nunique()), "median": float(g.value.median()),
                "min": float(g.value.min()), "max": float(g.value.max())} for d, g in gp.groupby("design")}
    priors["evidence_base"] = {"n_studies": int(len(studies)), "n_rct": int((studies.design == "rct").sum()),
                               "n_quasi": int((studies.design == "quasi_experimental").sum()),
                               "share_bridging_yes": float((studies.bridging == "yes").mean())}

    # Figure 1: evidence map heatmap (n studies, share positive) for main designs
    designs = ["rct", "quasi_experimental", "pre_post", "correlational"]
    doms = o.domain.value_counts().index.tolist()
    fig, ax = plt.subplots(figsize=(10, 0.45 * len(doms) + 2), dpi=100)
    M = np.full((len(doms), len(designs)), np.nan); N = np.zeros_like(M)
    for i, d in enumerate(doms):
        for j, de in enumerate(designs):
            g = em[(em.domain == d) & (em.design == de)]
            if len(g):
                M[i, j] = g.positive.iloc[0]; N[i, j] = g.n.iloc[0]
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i in range(len(doms)):
        for j in range(len(designs)):
            if N[i, j]:
                ax.text(j, i, f"{int(N[i, j])}\n{M[i, j]:.0%}", ha="center", va="center", fontsize=8.5,
                        color="white" if M[i, j] > 0.6 else "#0b0b0b")
    ax.set_xticks(range(len(designs)), ["Randomized", "Quasi-experimental", "Pre-post", "Correlational"])
    ax.set_yticks(range(len(doms)), [d.replace("_", " ") for d in doms])
    ax.set_title("Youth mentoring evidence map: studies (top) and share reporting positive results (bottom)", loc="left", fontsize=11.5)
    fig.colorbar(im, ax=ax, label="Share of studies reporting a positive result", shrink=0.7)
    fig.text(0.01, 0.005, "Coded from ERIC abstracts (1965-2023) by two independent AI coders + adjudicator. Vote counts are not effect sizes; "
             "positive-result publication bias likely. Verify before external use.", fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "evidence_map.png", dpi=150)
    plt.close(fig)

    if len(es) and "ess" in dir() and len(ess):
        e2 = ess.sort_values("median")
        fig, ax = plt.subplots(figsize=(9.5, 0.5 * len(e2) + 2), dpi=100)
        y = np.arange(len(e2))
        ax.hlines(y, e2.p25, e2.p75, color="#2a78d6", lw=4, alpha=0.5, label="Middle half of reported effects")
        ax.plot(e2["median"], y, "o", color="#2a78d6", label="Median")
        ok = e2.pooled_re.notna()
        ax.errorbar(e2.pooled_re[ok], y[ok] + 0.25, xerr=[(e2.pooled_re - e2.pooled_re_low)[ok], (e2.pooled_re_high - e2.pooled_re)[ok]],
                    fmt="D", color="#eb6834", ms=5, label="Random-effects pooled (studies with sample size)")
        ax.axvline(0, color="#52514e", lw=0.8)
        ax.set_yticks(y, [f"{d.replace('_', ' ')} (n={n})" for d, n in zip(e2.domain, e2.n_effects)])
        ax.set_xlabel("Standardized effect size (d or g) reported in abstracts")
        ax.legend(frameon=False, fontsize=8.5, loc="lower right")
        ax.set_title("Reported mentoring effect sizes by outcome domain", loc="left", fontsize=12)
        fig.text(0.01, 0.005, "Only effects stated numerically in abstracts; small or null effects are less likely to be reported there. Verify before external use.",
                 fontsize=7.5, color="#52514e")
        fig.tight_layout(rect=(0, 0.03, 1, 1))
        fig.savefig(OUT / "effect_sizes.png", dpi=150)
        plt.close(fig)
    print(json.dumps({k: v for k, v in priors.items() if k != "effect_sizes_from_abstracts"}, indent=1, default=str))

(OUT / "priors.json").write_text(json.dumps(priors, indent=2, default=str))
