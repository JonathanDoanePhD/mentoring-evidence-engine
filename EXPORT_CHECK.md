# Export check (mentoring-evidence-engine)

Size: 4.7 MB. Requirements: pandas==3.0.5, numpy==2.5.3, matplotlib==3.11.2.

Items to review:

- `output/study_features.csv` column `n_studies` has 8 cell(s) with n < 10: review for suppression
- `output/effect_size_summary.csv` column `n_effects` has 5 cell(s) with n < 10: review for suppression
- `output/effect_size_summary.csv` column `n_studies` has 6 cell(s) with n < 10: review for suppression
- `output/effect_size_summary.csv` column `n_with_sample_size` has 4 cell(s) with n < 10: review for suppression
- `output/effect_size_summary.csv` column `rct_n` has 5 cell(s) with n < 10: review for suppression
- `output/effect_sizes.csv` column `n_youth` has 3 cell(s) with n < 10: review for suppression
- `output/evidence_map.csv` column `n` has 8 cell(s) with n < 10: review for suppression
- `output/reviews.csv` column `n_studies` has 12 cell(s) with n < 10: review for suppression
- `output/graduation_college.csv` column `n_youth` has 1 cell(s) with n < 10: review for suppression
- `output/positive_by_rigor.csv` column `n_findings` has 1 cell(s) with n < 10: review for suppression
- `output/positive_by_rigor.csv` column `n_studies` has 1 cell(s) with n < 10: review for suppression

Reviewed: the small counts are numbers of studies or published study sample sizes, not counts of people in a dataset, so no suppression is needed.
