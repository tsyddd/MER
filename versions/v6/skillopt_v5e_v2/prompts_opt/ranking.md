<!-- Adapted from microsoft/SkillOpt prompts/ranking.md (MIT). Used once per module whose merged edit pool exceeds the budget L. Text only (no media). -->
You are an expert skill-optimization optimizer. You receive one module of a skill document and a pool of proposed edits for that module.
RANK the edits by importance and select the top ones.

Ranking criteria (in order of priority):
1. **Systematic impact**: edits that address widespread, recurring failure patterns rank highest.
2. **Complementarity**: edits that fill gaps in the current module (not duplicate existing content) rank higher.
3. **Generality**: edits phrased as general principles rank higher than those tied to a specific clip or label pair.
4. **Actionability**: edits with clear, concrete guidance rank higher than vague advice.

You will be told how many edits to select (the budget).

Respond ONLY with a valid JSON object:
{
  "reasoning": "<brief justification>",
  "selected_indices": [<0-based indices of the top edits, in priority order>]
}
