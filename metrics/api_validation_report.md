# GPT / Gemini PPCT validation

| Method | MER2024 | MELD | All80 | Audited |
|---|---:|---:|---:|---:|
| gpt | 77.50% (31/40) | 77.50% (31/40) | 77.50% (62/80) | 80/80 |
| gemini | 75.00% (30/40) | 60.00% (24/40) | 67.50% (54/80) | 80/80 |

Each sample follows perception, temporal/joint judgments, program graph, organization and final inference. Eight chronological frames and available subtitle are used. Gemini also receives audio; GPT audio is omitted because this endpoint rejects it.

Final output contains an evidence explanation and exactly one <answer>label</answer>. MER2024 retains six labels, MELD seven. Gold labels and prior model predictions are excluded from inference payloads. Structural repair feedback, when needed, contains only prior response and validation error.

These are balanced development subsets selected using five prior models, not untouched benchmark tests. The prior five-model comparison uses four frames, so this eight-frame result is not a controlled frame-matched comparison.

API identities are provider-reported aliases. Usage and timing cover recorded response artifacts only; see JSON for scope. Flow/format audit does not establish that every observation or explanation is factually correct.

Omni allows logged structural normalization and removal of invalid edges; GPT/Gemini retain strict validation with model-generated repair feedback. Omni direct and PPCT results remain pending until separately completed and audited.
