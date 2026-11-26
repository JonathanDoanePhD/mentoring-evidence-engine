export const meta = {
  name: 'mentoring-evidence-adjudicate',
  description: 'Adjudicate coder disagreements on design, rigor, outcomes and effect sizes, writing validated JSON to disk',
  phases: [{ title: 'Adjudicate', detail: 'one agent per batch of disagreements' }],
}
const ROOT = '/home/user/claude_projects/projects/08-mentoring-evidence-engine'
const SCHEMA = {
  type: 'object',
  properties: { batch: { type: 'string' }, n_records: { type: 'integer' }, valid: { type: 'boolean' }, issues: { type: 'string' } },
  required: ['batch', 'n_records', 'valid', 'issues'],
}
const prompt = (b) => `You are the adjudicator in a double-coded systematic evidence map of youth mentoring research.

1. Read the coding rules in ${ROOT}/docs/protocol.md (section "Stage 2: Coding").
2. Read ${ROOT}/data/interim/batches/adjudicate/${b}.jsonl. Each line has the study record (title, abstract, descriptors...) plus "coder_a" and "coder_b" codings that disagree on at least one key field (design, rigor, outcome directions or effect sizes).
3. For each record, read the abstract IN FULL and produce ONE final coding with the same keys as the coders (id, design, rigor, n_youth, country, setting, format, mentor_type, targets, grade_band, program_name, duration_months, frequency, bridging, outcomes, effect_sizes, review_details, notes). Decide every field from the abstract itself; where the coders agree and the abstract supports it, keep that value. Code only what the abstract states. Effect-size sign: positive = better for youth (a dropout rate that falls is a positive graduation_persistence value); treatment-minus-comparison rate differences are pct_points with both rates in the note.
4. Write the JSON list to ${ROOT}/data/coded/adjudicate/${b}.json and run: python3 -I ${ROOT}/scripts/validate.py adjudicate ${ROOT}/data/coded/adjudicate/${b}.json — fix until VALID.
5. Keep ALL temporary files (scripts, chunk printouts) in your PRIVATE temporary folder ${ROOT}/data/interim/tmp/${b}/ (create it). Never use the shared scratchpad or /tmp: other agents run at the same time and would overwrite your files. Build the output by matching each record's id, never by position. Do not modify any other files. Do not run git.
Return counts; valid=true only if the validator printed VALID.`

log(`Adjudicating ${args.batches.length} batch(es)`)
const results = await parallel(args.batches.map(b => () =>
  agent(prompt(b), { label: `adjudicate ${b}`, phase: 'Adjudicate', schema: SCHEMA })))
return results.filter(Boolean)
