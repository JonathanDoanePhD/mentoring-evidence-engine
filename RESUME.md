# How to resume the pipeline

Every agent writes its own validated output file to `data/coded/`, so finished work is never
lost and any stage can be resumed from where it stopped. Run from the repo root.

1. **Rebuild inputs if the container is new** (raw data and batch files are not committed):
   ```bash
   python3 -I scripts/fetch_data.py .
   python3 -I scripts/01_extract_mentoring_records.py
   python3 -I scripts/02_prefilter.py
   python3 -I scripts/03_make_screen_batches.py      # deterministic: same batches every time
   python3 -I scripts/03b_make_supplement_batch.py   # adds supplementary batch 62 (protocol v1.2)
   ```
2. **See what is pending:** `python3 -I scripts/status.py` (or `--json`).
3. **Screening:** launch `scripts/workflows/screen.js` with
   `args: {"model": "sonnet", "batches": [<pending screen batches>]}` (Sonnet was calibrated against the
   reference model: kappa 0.87 on include/exclude; see protocol v1.1).
4. **Coding (after screening is complete):** `python3 -I scripts/04_make_code_batches.py`, then
   launch `scripts/workflows/code.js` with `args: {"model": "sonnet", "coder_a": [...], "coder_b": [...]}`
   (pending lists from `status.py --json`).
5. **Adjudication:** `python3 -I scripts/05_reconcile.py` writes adjudication batches for
   disagreements (one per coding batch, created as soon as both coders finish it, so this can run
   alongside coding; rerun reconcile after each coding wave); launch `scripts/workflows/adjudicate.js` with `args: {"batches": [...]}` (default model, no override); rerun
   `05_reconcile.py` to produce the final coded dataset.
6. **Analysis:** `python3 -I scripts/06_report.py`.
7. Commit `data/coded/` and `output/` after each wave (`git status` first: `data/interim/`
   and `data/raw/` must never be staged).
