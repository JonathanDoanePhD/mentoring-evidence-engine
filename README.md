# 08 - Mentoring Evidence Engine

**Question:** What does the research indexed in ERIC (1965-2023) say about youth mentoring:
which outcomes it affects, for whom, with what program features, and how rigorously it has
been studied? The answer feeds Project 03 (effect sizes for power and simulation) and Project
07 (the graduation effect behind the break-even model).

**Status:** first full pass complete (2026-11-19). All three stages are done, and every output
can be rebuilt by the scripts. Before external use, a person must audit a sample of records
against the full papers (see Next steps).

> **Exploratory, AI-assisted research.** Screening and coding were done by Claude agents
> following [docs/protocol.md](docs/protocol.md), with validation, calibration and agreement
> checks. Every figure below comes from **abstracts**, not full papers. All figures need
> verification against the original studies before they go to funders or the public.

## Key findings

1. **The stronger the study, the weaker the result.** Across 1,383 coded outcome findings, 84%
   are positive in the weakest studies (rigor 1-2), 75% at rigor 3 and 56% at rigor 4-5. Null
   findings go from 5% to 27%. Graduation and persistence show the same drop: 86%, then 81%,
   then 50% positive.
   - Randomized trials report positive results least often in nearly every outcome domain
     (`output/evidence_map.png`).
   - Much of the positive literature is therefore likely to overstate what mentoring does.
     The rigorous half is what should set expectations.
2. **Credible effects are small.** Standardized academic effects stated in abstracts pool to
   about **d = 0.27** (random effects, 5 studies, 95% CI 0.21-0.33). The median from
   randomized trials is 0.22.
   - The one meta-analysis that reports a pooled value in its abstract (school-based mentoring
     for adolescents, 8 studies) finds **g = 0.09**, mostly nonsignificant.
   - This is in line with Project 03's planning advice of about 0.1-0.15 SD.
3. **Graduation evidence is thin where it matters most.** 139 records report graduation or
   persistence outcomes, but only 14 are randomized. Gains in percentage points fall as design
   gets stronger:

   | Design | Median gain | Studies |
   |---|---|---|
   | Comparison with national or historical averages | 35 points | 4 |
   | Pre-post | 21 points | 2 |
   | Comparison group (quasi-experimental) | 15 points | 7 |
   | Randomized | 5 points (range 4-15) | 1 |

   The single randomized source is a college coaching program, not classic youth mentoring.
   The K-12 randomized trials are mostly null: two Check & Connect trials and the Quantum
   Opportunity Program found no effect on graduation, Twelve Together (peer groups) found a
   benefit, and a coaching-plus-cash trial helped only young women. A residential program with a
   mentoring phase for out-of-school youth (National Guard Youth ChalleNGe) found benefits.
4. **Bridging programs look better, even within rigor bands.** These are programs that
   deliberately connect youth to people, networks or careers beyond their usual circles (15%
   of studies).
   - At rigor 4-5, 79% of their findings are positive, against 52% for other programs. The gap
     is similar at lower rigor (`output/bridging_by_rigor.csv`).
   - At rigor 4-5 this rests on only 16 studies, and the rating comes from abstracts. Treat it
     as a lead for Projects 02 and 04 (cross-class ties), not a conclusion.
5. **The field under-reports what programs actually do.** Mentoring format is unclear in 52% of
   studies, mentor type in 51%, and meeting frequency is not reported in 90%. That makes
   abstracts a poor source for dose-response questions, and it is why Project 03's instrument
   records dose directly.
6. **The research base has grown and shifted to college.** 38% of studies concern
   undergraduates, mostly retention and STEM programs. 22% concern high school, 11% middle
   school and 8% elementary. Most studies (and most randomized trials) date from 2010 or later.

## How it works

| Stage | What happens | Scale |
|---|---|---|
| 0. Extract | Stream all 1,981,015 ERIC records (bulk XML, 1965-2023); keep the 24,228 that mention mentoring | code |
| 0. Tier | Rules sort records by youth and evaluation signals: Tier A 11,201; Tier B 5,233; Tier X (adult/professional mentoring) 7,647 | code |
| 1. Screen | Agents apply the protocol's inclusion rules to every core record (8,174: mentoring in title or descriptors), to fixed-seed recall samples from the other tiers (850), and to a supplementary batch (114 records mentioning mentoring 3+ times) | 62 batches, 9,138 records |
| 2. Code | Two independent coders per included study extract design, rigor (1-5), sample, setting, format, mentor type, targets, grade band, dose, bridging, outcome directions by domain and stated effect sizes. Disagreements on key fields go to an adjudicator | 38 batches × 2 coders; 322 adjudicated |
| 3. Report | Evidence map, recall estimate, coding reliability, rigor gradient, effect-size synthesis, graduation evidence, priors for Projects 03 and 07 | `scripts/06_report.py` |

## Stage 1 results (screening)

- **9,138 records screened.** 868 are youth mentoring outcome studies and 92 are reviews or
  meta-analyses. Another 1,740 are about youth mentoring without quantitative mentee outcomes.
- The rest were excluded:
  - 4,420 concern adult or professional mentoring (mostly new teachers, faculty, graduate
    students).
  - 1,130 mention mentoring only incidentally.
  - 888 were excluded for other reasons.
- **In-scope set for coding: 935 records** (839 primary studies and 96 reviews after coding).
- **Recall:** the fully screened, in-scope set holds an estimated **78%** of all relevant ERIC
  records. Most of the rest are multi-component programs (college retention, STEM pipelines)
  where mentoring is one ingredient, and they are out of scope by design (protocol v1.2). No
  relevant records were found in the adult/professional tier sample.

## Stage 2 results (coding)

- **Reliability** of two independent coders on 935 records (`output/coding_reliability.csv`):

  | Field | Agreement | Cohen's kappa |
  |---|---|---|
  | Design | 93% | 0.91 |
  | Grade band | 93% | 0.91 |
  | Rigor | 85% exact; 99% within 1 point | 0.79 |
  | Outcome directions (11 domains) | 88-99% | 0.71-0.93 |
  | Effect sizes identical | 97% | - |
  | Setting | 87% | 0.83 |
  | Mentor type | 83% | 0.77 |
  | Bridging | 82% | 0.68 |
  | Country | 80% | 0.65 |
  | Format | 73% | 0.63 |

- **Adjudication:** 322 records (34%) disagreed on design, rigor (by more than 1 point),
  outcome directions or effect sizes. A third agent using the stronger default model resolved
  them from the abstract. The other 613 records keep the agreed values.
- **Sign check:** no effect size contradicts its coded direction
  (`output/review_sign_conflicts.csv` is empty), and no negative graduation gains were found.
  The adjudicator corrected one sign slip, where fewer absences had been coded as negative,
  before this check ran.

## Priors for other projects (`output/priors.json`)

| Project | Input | Value from this evidence map | Use |
|---|---|---|---|
| 03 | Planning effect size | academic d ≈ 0.22-0.27 in abstracts; g = 0.09 in the one pooled school-mentoring meta-analysis | Keep planning around **0.1-0.15 SD**. The abstract figures are upper bounds because small or null effects rarely reach abstracts |
| 07 | High school graduation effect | no randomized K-12 estimate in percentage points; randomized college coaching 4-15 points (median 5); K-12 trials mostly null (3 null, 1 positive, 1 mixed) | Keep the **1.5-point central value and 0-4 range**. The break-even of about 1 point is plausible but not established |

## Outputs

| File | What |
|---|---|
| `output/prefilter_counts.csv` | Records per rule-based tier |
| `output/screening_summary.csv` | Decisions by stratum, weighted estimates, recall |
| `output/screening_calibration.csv` | Sonnet vs. reference agreement |
| `output/screening_alignment.csv` | Alignment score per batch |
| `output/coding_reliability.csv` | Agreement and kappa per coded field |
| `output/study_features.csv` | Distribution of design, rigor, decade, setting, format, mentor type, grade band, bridging, country, dose, targets |
| `output/evidence_map.csv`, `.png` | Studies and share positive by outcome domain × design |
| `output/positive_by_rigor.csv` | Rigor gradient, all domains and per domain |
| `output/bridging_by_rigor.csv` | Bridging vs. other programs within rigor bands |
| `output/effect_sizes.csv` | Every numeric effect stated in an abstract |
| `output/effect_size_summary.csv`, `effect_sizes.png` | Median, IQR and random-effects pooled d/g by domain |
| `output/graduation_college.csv` | All graduation/persistence and college-access findings |
| `output/reviews.csv` | Reviews and meta-analyses with stated pooled values |
| `output/review_sign_conflicts.csv`, `review_negative_graduation_effects.csv` | Lists for manual sign review (currently empty) |
| `output/priors.json` | Machine-readable summary for Projects 03 and 07 |
| `data/coded/screen/`, `code/`, `adjudicate/` | All agent decisions (no abstract text; short paraphrased notes) |
| `data/coded/final_coded.json` | Final coded dataset (935 records) |

## Columns in `final_coded.json`

`id` (ERIC ID), `design`, `rigor` (1-5), `n_youth`, `country`, `setting`, `format`,
`mentor_type`, `targets` (list), `grade_band`, `program_name`, `duration_months`, `frequency`,
`bridging`, `outcomes` (domain → positive/null/mixed/negative), `effect_sizes` (list of
domain, metric, value, note), `review_details`, `notes` (paraphrase, ≤25 words), `resolution`
(agreed / adjudicated). Definitions are in [docs/protocol.md](docs/protocol.md).

## Caveats

- **Abstracts only.** Directions and numbers are what abstracts state. Abstracts favor
  positive and significant results, so vote counts and stated effect sizes overstate effects.
- **Vote counts are not effect sizes.** "Share positive" counts findings, not magnitudes, and
  ignores sample size.
- **Records are not independent studies.** ERIC often holds several documents about one
  evaluation (a report, an executive summary and a clearinghouse review). National Guard Youth
  ChalleNGe appears 4 times. Counts are of records, not of distinct trials.
- **Rigor ratings come from abstract descriptions,** so a well-designed study with a vague
  abstract can be under-rated.
- **Scope:** about 78% of relevant ERIC records. Multi-component programs where mentoring is
  peripheral are excluded by design. ERIC also misses some psychology, criminal-justice and
  social-work literature.
- **AI coding:** reliability is high on core fields, but the coders are language models. A
  person must audit a random sample against full papers before any figure is used externally.

## Next steps

- **Human audit:** have a person check a random sample of 50 coded records (stratified by
  resolution) against the full papers, and check every effect in `effect_size_summary.csv`
  and the graduation table above. Record the results in this folder.
- **Deduplicate evaluations:** group multiple records of the same trial before pooling.
- **Full-text extraction:** for the 75 randomized trials and the 8 meta-analyses, extract
  effect sizes from open-access full texts where available.
- **Bridging lead:** test the bridging gap with full-text rigor ratings. If it holds, it
  directly supports the "bridging adults" theme of Projects 02, 04 and 07.

## Rebuild / continue

See [RESUME.md](RESUME.md). ERIC raw data (~1 GB) and batch files with abstract text live in
`data/raw/` and `data/interim/`, which are not committed. Only coded features are committed.
With the coded files in place, `python3 -I scripts/05_reconcile.py` then
`python3 -I scripts/06_report.py` rebuild every output.

## License, citation and data terms

- **Code:** MIT (see `LICENSE`). **Outputs:** CC BY 4.0, subject to the source terms below.
- **Cite this project as:** JonathanDoanePhD (2026). *Mentoring Evidence Engine*. https://github.com/JonathanDoanePhD/mentoring-evidence-engine
- **Data sources and terms** (from `data/sources.csv`; recorded versions and checksums in `data/sources.lock.csv`):

| Source | Terms |
|---|---|
| ERIC (Institute of Education Sciences) bulk XML records 1965-1979 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC (Institute of Education Sciences) bulk XML records 1980-1989 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC (Institute of Education Sciences) bulk XML records 1990-1999 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC (Institute of Education Sciences) bulk XML records 2000-2009 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC (Institute of Education Sciences) bulk XML records 2010-2014 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC (Institute of Education Sciences) bulk XML records 2015-2019 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC (Institute of Education Sciences) bulk XML records 2020-2023 | ERIC metadata is U.S. government work; abstracts may be author/publisher text - store coded features only (raw data never committed) |
| ERIC Thesaurus (descriptor vocabulary) | U.S. government work (public domain) |

Built with AI assistance (Claude). Exploratory research: every statistic needs checking against its original source
before it appears in funder reports, grant applications or public material.

## Status and limitations

Published 2026-11-26 as exploratory research. The analysis is complete and reproducible, but these checks have **not yet been done**, so treat figures as provisional:

- Statistics in this README and in `output/` have not been independently checked against their original sources.
- A person audits a random sample of 50 coded studies against the full papers.
- Merge multiple ERIC records of the same trial before pooling.
- Verify every effect size cited.
