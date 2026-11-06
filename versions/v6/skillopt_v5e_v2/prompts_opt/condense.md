<!-- Adapted from microsoft/SkillOpt prompts/rewrite_skill.md (MIT). Used when one dataset section would exceed its length cap. Text only. -->
You are an expert skill-document rewriter. You receive ONE dataset section of a skill document (three modules: first / relook / reflect),
the length cap of the section and, optionally, new edits that should be incorporated.

Rewrite the section so that it is at most the cap (in characters) and keeps the effective guidance:
1. Merge duplicates and near-duplicates; prefer one clear rule over several overlapping ones.
2. Keep rules that name an observable cue separating two labels; drop vague advice and rules without a cue.
3. Incorporate the new edits (if any) in the module they name.
4. Keep each module's scope (first = A cues + B when to name an uncertain point; relook = C; reflect = D).
5. Do not add new claims; no sample ids, quotes, numbers, default-label rules or output-format wording; only this dataset's label names.

Respond ONLY with a valid JSON object:
{
  "reasoning": "<what was merged / dropped>",
  "modules": {"first": "<text>", "relook": "<text>", "reflect": "<text>"}
}
