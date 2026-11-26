export const meta = {
  name: 'mentoring-evidence-code',
  description: 'Double-code included youth mentoring studies (two independent coders per batch), writing validated JSON to disk',
  phases: [{ title: 'Code', detail: 'coder A and coder B independently, one agent per batch' }],
}
const ROOT = '/home/user/claude_projects/projects/08-mentoring-evidence-engine'
const SCHEMA = {
  type: 'object',
  properties: {
    batch: { type: 'string' }, coder: { type: 'string' }, n_records: { type: 'integer' },
    n_with_effect_sizes: { type: 'integer' }, valid: { type: 'boolean' }, issues: { type: 'string' },
  },
  required: ['batch', 'coder', 'n_records', 'n_with_effect_sizes', 'valid', 'issues'],
}
const prompt = (coder, b) => `You are ${coder === 'coder_a' ? 'Coder A' : 'Coder B'} in a double-coded systematic evidence map of youth mentoring research. Another coder codes the same records independently: do NOT open or read anything under ${ROOT}/data/coded/code/ except your own output file.

1. Read the coding rules in ${ROOT}/docs/protocol.md (section "Stage 2: Coding"). Follow them exactly and code only what the abstract and metadata state.
2. Read the input batch ${ROOT}/data/interim/batches/code/${b}.jsonl (one JSON record per line). Read EVERY abstract IN FULL; never truncate. Effect sizes, sample sizes and designs are often in the last sentences.
3. For every record, produce one object with exactly these keys:
   id, design, rigor, n_youth, country, setting, format, mentor_type, targets, grade_band, program_name, duration_months, frequency, bridging, outcomes, effect_sizes, review_details, notes
   - outcomes: {domain: direction} only for domains the abstract reports measuring.
   - effect_sizes: only numbers stated in the abstract (list, may be empty).
   - review_details: object for reviews ({"n_studies", "pooled_metric", "pooled_value"}), else null.
   - notes: at most 20 words in your own words; never copy abstract text.
4. Write the JSON list to ${ROOT}/data/coded/code/${coder}/${b}.json (create folders if needed; a short Python script is fine).
5. Run: python3 -I ${ROOT}/scripts/validate.py code ${ROOT}/data/coded/code/${coder}/${b}.json and fix until it prints VALID.
6. Keep ALL temporary files (scripts, chunk printouts) in your PRIVATE temporary folder ${ROOT}/data/interim/tmp/${b}/ (create it). Never use the shared scratchpad or /tmp: other agents run at the same time and would overwrite your files. Build the output by matching each record's id, never by position. Do not modify any other files. Do not run git.
Return counts from your final valid file; valid=true only if the validator printed VALID. In "issues", confirm you read every abstract in full and note any hard calls.`

const items = [
  ...(args.coder_a || []).map(b => ({ coder: 'coder_a', b })),
  ...(args.coder_b || []).map(b => ({ coder: 'coder_b', b })),
].sort((x, y) => x.b === y.b ? x.coder.localeCompare(y.coder) : x.b.localeCompare(y.b))  // pairs finish together
log(`Coding ${items.length} coder-batches`)
const results = await parallel(items.map(it => () =>
  agent(prompt(it.coder, it.b), { label: `${it.coder} ${it.b}`, phase: 'Code', schema: SCHEMA, ...(args.model ? { model: args.model } : {}) })))
const ok = results.filter(Boolean)
log(`Done: ${ok.filter(r => r.valid).length}/${items.length} valid`)
return ok
