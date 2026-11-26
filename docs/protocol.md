# Protocol: Mentoring Evidence Engine

Version 1.0 (2026-11-14). Agents follow this document exactly. Changes get a new version and
a note in the changelog at the bottom.

## Question

What does the research indexed in ERIC (1965-2023) say about the effects of **youth mentoring**:
on which outcomes, for whom, with what program features, and with how much rigor? Results
feed Project 03 (effect sizes for power and simulation) and Project 07 (the graduation effect
in the cost-benefit model).

## Stage 1: Screening (one decision per record)

Read the title, abstract and descriptors. Choose exactly one **decision**:

| Decision | Use when |
|---|---|
| `include_outcome` | **Youth** mentoring (definition below) **and** the study reports quantitative outcomes for mentees: effects, comparisons, pre-post change, or associations between mentoring and youth outcomes |
| `include_review` | A meta-analysis, systematic review or research synthesis **of youth mentoring** |
| `include_other` | About youth mentoring but no quantitative mentee outcomes (qualitative, descriptive, program guide, mentor-side only) |
| `exclude_adult` | Mentees are adults in professional roles or graduate training: teachers (incl. new or preservice teachers), faculty, graduate/doctoral students, nurses, physicians, employees, administrators |
| `exclude_not_mentoring` | "Mentor" is incidental, or the intervention is tutoring/coaching/advising with no mentoring relationship described |
| `exclude_other` | Anything else (e.g., not a study or document about mentoring youth) |

**Youth:** ages about 5-24, including K-12 students, out-of-school youth, and undergraduate
college students (tag the population). **Mentoring:** a relationship in which an older or more
experienced person (adult or older peer) offers guidance and support to a younger person. It
includes one-to-one, group, peer/cross-age, e-mentoring, school- or community-based, career
and academic mentoring, and studies of natural (informal) mentors. When unsure between
include and exclude, choose the include category and mark `confidence: "low"`.

Per record, return:

```json
{"id": "EJ1210671", "decision": "include_outcome", "population": "k12_mixed",
 "confidence": "high", "reason": "Natural mentors and youth psychosocial outcomes, school year"}
```

`population`: one of `k12_elementary`, `k12_middle`, `k12_high`, `k12_mixed`, `college_undergrad`,
`out_of_school_youth`, `youth_other`, `adult`, `unclear`. `confidence`: `high` / `medium` / `low`.
`reason`: at most 15 words, in your own words (do not copy abstract text).

## Stage 2: Coding (included outcome studies and reviews)

Two agents code each record independently; a third adjudicates disagreements on key fields.
Code **only what the abstract and metadata say**; use `null`/`"not_reported"` rather than guess.

| Field | Values |
|---|---|
| `design` | `rct`, `quasi_experimental` (comparison group, matched or not), `pre_post` (no comparison group), `correlational` (associations, incl. natural mentoring surveys), `review`, `other` |
| `rigor` | 1-5. 1 = descriptive/anecdotal; 2 = pre-post, no comparison; 3 = comparison group, no matching or controls described; 4 = matched/statistically controlled comparison or longitudinal with controls; 5 = randomized. Reviews: 4 if a quantitative meta-analysis, 3 otherwise |
| `n_youth` | integer or null |
| `country` | e.g. `US`, `UK`, `Canada`, `Australia`, `other`, `unclear` |
| `setting` | `school_based`, `community_based`, `online`, `workplace_career`, `college_campus`, `mixed`, `unclear` |
| `format` | `one_to_one`, `group`, `peer_cross_age`, `mixed`, `natural_mentor`, `unclear` |
| `mentor_type` | `adult_volunteer`, `paid_staff`, `college_student`, `older_peer`, `teacher_school_staff`, `natural_informal`, `mixed`, `unclear` |
| `targets` | list from: `low_income`, `racial_ethnic_minority`, `at_risk_behavior`, `juvenile_justice`, `foster_care`, `first_generation`, `disability`, `girls_women_stem`, `stem_general`, `lgbtq`, `gifted`, `immigrant_ell`, `rural`, `urban`, `general` |
| `grade_band` | `elementary`, `middle`, `high`, `k12_mixed`, `college`, `out_of_school`, `unclear` |
| `program_name` | short name if named (e.g. "Big Brothers Big Sisters"), else null |
| `duration_months` | number or null (program or relationship length) |
| `frequency` | `weekly_or_more`, `biweekly`, `monthly`, `other`, `not_reported` |
| `bridging` | `yes` if the program deliberately connects youth to people, networks or careers beyond their usual circles (career mentors, workplace exposure, introductions, college access networks); `no`; `unclear` |
| `outcomes` | object; for each domain measured give a direction: `positive`, `null`, `negative`, `mixed`. Omit domains not measured. Domains: `academic_achievement`, `engagement_attendance`, `graduation_persistence`, `college_access_enrollment`, `self_efficacy_confidence`, `belonging_connectedness`, `psychosocial_other`, `behavior_delinquency`, `mental_health`, `career_employment`, `relationships_social` |
| `effect_sizes` | list of numbers stated in the abstract only: `{"domain": ..., "metric": "d" | "g" | "or" | "r" | "pct_points" | "other", "value": number, "note": "<=10 words"}`; empty list if none. **When the abstract gives a rate for the mentored group and a comparison group (e.g. 53% vs 17% retained), record the difference as `pct_points` (36) and put both rates in the note.** Use `other` only for numbers that are not effects or differences. **Sign: positive = better for youth** (e.g. a dropout rate falling from 7.2% to 1.6% is +5.6 under `graduation_persistence`) |
| `review_details` | reviews only: `{"n_studies": int|null, "pooled_metric": str|null, "pooled_value": number|null}` |
| `notes` | at most 20 words, own words |

## Quality control

- Every output file is checked by `scripts/validate.py` (schema, IDs match the batch, allowed
  values) before an agent reports success.
- Screening recall: random samples from records the rules put in lower tiers are screened too;
  `scripts/report.py` estimates how many relevant studies the rules missed.
- Coding reliability: two independent coders per record; agreement (percent and Cohen's kappa)
  reported per field; disagreements on `design`, `rigor` (difference > 1), outcome directions
  and effect sizes go to an adjudicator.
- A person should audit a random sample of coded records against the full papers before any
  figure is used externally.

## Privacy and copyright

ERIC records are about publications, not participants; no personal data about youth is
coded. Author names are not stored in coded outputs. Abstract text stays in `data/interim/`
(not committed); committed outputs contain only coded features and short paraphrased notes.

## Changelog

- 1.0 (2026-11-14): initial protocol.
- 1.1 (2026-11-14): screening batches 1-5 used the session's default model; batches 6-61 use
  Sonnet (cheaper) after calibration. Re-screening batches 1-2 with Sonnet agreed with the
  reference on 97% of include/exclude decisions (Cohen's kappa 0.87, n = 300); all 9
  disagreements were borderline cases (`output/screening_calibration.csv`). Coding and
  adjudication keep the default model. A pilot of batch 1 showed the screener skimming long
  abstracts, so the instructions now require reading every abstract in full.
- 1.2 (2026-11-14): scope and recall. Interim recall estimates (6,000 records screened) showed
  roughly 30% of relevant records fall outside the core stratum, mostly multi-component
  programs where mentoring is one ingredient (mentioned once). The evidence map is scoped to
  studies where mentoring is central (core stratum: mentoring in title or descriptors), plus a
  supplementary batch (62) of non-core records that mention mentoring 3+ times. The share of
  related studies outside scope is reported in `output/screening_summary.csv`.
- 1.3 (2026-11-14): coding pilot showed group rates coded as raw values; rule added to record
  treatment-minus-comparison differences as `pct_points`. Coders use Sonnet (two independent
  coders); the adjudicator uses the default model.
- 1.4 (2026-11-14): sign convention for effect sizes made explicit (positive = better for
  youth) after the adjudication pilot recorded a falling dropout rate as negative. The report
  lists negative graduation/persistence values for manual review.
