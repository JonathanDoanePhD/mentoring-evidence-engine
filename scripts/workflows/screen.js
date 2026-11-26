export const meta = {
  name: 'mentoring-evidence-screen',
  description: 'Screen ERIC abstracts for youth mentoring studies, one agent per batch, writing validated JSON to disk',
  phases: [{ title: 'Screen', detail: 'one agent per batch of ~150 abstracts' }],
}
const ROOT = '/home/user/claude_projects/projects/08-mentoring-evidence-engine'
const SCHEMA = {
  type: 'object',
  properties: {
    batch: { type: 'string' },
    n_records: { type: 'integer' },
    n_include_outcome: { type: 'integer' },
    n_include_review: { type: 'integer' },
    n_include_other: { type: 'integer' },
    valid: { type: 'boolean' },
    issues: { type: 'string' },
  },
  required: ['batch', 'n_records', 'n_include_outcome', 'n_include_review', 'n_include_other', 'valid', 'issues'],
}
const OUTDIR = (args && args.outdir) || 'screen'
const prompt = (b) => `You are screening research abstracts for a systematic evidence map of youth mentoring.

1. Read the screening rules in ${ROOT}/docs/protocol.md (section "Stage 1: Screening"). Follow them exactly.
2. Read the input batch ${ROOT}/data/interim/batches/screen/${b}.jsonl (one JSON record per line: id, year, title, abstract, descriptors, levels, types).
   Read EVERY abstract IN FULL. Never truncate or skim: if you print records with a script, print them about 20 at a time with the complete abstract text, and go through all chunks. Study design and outcomes are often in the last sentences.
3. For EVERY record, decide using only that record's text. Produce a JSON list with one object per record, in the same order:
   {"id": ..., "decision": ..., "population": ..., "confidence": ..., "reason": ...}
   Allowed values are listed in the protocol. "reason" is at most 15 words in your own words; never copy abstract text.
4. Write the list to ${ROOT}/data/coded/${OUTDIR}/${b}.json (create the folder if needed). Write it with a short Python script if that is easier than hand-writing JSON.
5. Run: python3 -I ${ROOT}/scripts/validate.py screen ${ROOT}/data/coded/${OUTDIR}/${b}.json
   If it prints INVALID, fix the file and re-run until it prints VALID.
6. Keep ALL temporary files (scripts, chunk printouts) in your PRIVATE temporary folder ${ROOT}/data/interim/tmp/${b}/ (create it). Never use the shared scratchpad or /tmp: other agents run at the same time and would overwrite your files. Build the output by matching each record's id, never by position. Do not modify any other files. Do not run git.
Return the counts for this batch (from your final valid file) and valid=true only if the validator printed VALID. In "issues", confirm that you read every abstract in full and list any borderline records.`

const batches = args.batches
log(`Screening ${batches.length} batch(es)`)
const results = await parallel(batches.map((b) => () =>
  agent(prompt(b), { label: `screen ${b}`, phase: 'Screen', schema: SCHEMA, effort: 'low', ...(args.model ? { model: args.model } : {}) })))
const ok = results.filter(Boolean)
log(`Done: ${ok.filter(r => r.valid).length}/${batches.length} valid`)
return ok
