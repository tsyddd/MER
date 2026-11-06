<!-- Adapted from microsoft/SkillOpt prompts/merge_final.md (MIT). Changes: `module` field kept on every edit; no protected regions. Text only (no media). -->
You are a skill-edit coordinator performing the FINAL merge. You receive two pre-merged patch groups:
1. **Failure-driven patches** (corrective, high priority)
2. **Success-driven patches** (reinforcement, lower priority)

Merge guidelines:
1. **FAILURE PATCHES TAKE PRIORITY**: the primary goal is to fix failures. Keep failure-driven edits unless they directly conflict with a
   well-supported success pattern.
2. **Deduplicate**: if a failure edit and a success edit cover the same point, keep the failure version.
3. **Preserve success insights**: include success edits that cover patterns NOT addressed by failure edits.
4. **Higher-level merges represent broader consensus**: edits that survived previous merge rounds get priority.
5. Carry forward `support_count`, `source_type` and the `module` of every edit.

Respond ONLY with a valid JSON object:
{
  "reasoning": "<summary of priority decisions>",
  "edits": [
    {"module": "first|relook|reflect", "op": "append|insert_after|replace|delete", "target": "<if needed>", "content": "<text>",
     "support_count": <integer>, "source_type": "failure|success"}
  ]
}
