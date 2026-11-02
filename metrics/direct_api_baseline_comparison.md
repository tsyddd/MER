# Direct API baseline vs PPCT

| Method | MER2024 | MELD | All80 | Audited |
|---|---:|---:|---:|---:|
| direct/gpt | 60.00% (24/40) | 70.00% (28/40) | 65.00% (52/80) | 80/80 |
| ppct/gpt | 77.50% (31/40) | 77.50% (31/40) | 77.50% (62/80) | 80/80 |
| direct/gemini | 82.50% (33/40) | 67.50% (27/40) | 75.00% (60/80) | 80/80 |
| ppct/gemini | 75.00% (30/40) | 60.00% (24/40) | 67.50% (54/80) | 80/80 |

Same fixed 80 development samples and eight frames as PPCT. GPT: frames and available subtitle; Gemini: frames, original audio and available subtitle. Each direct request receives no graph, nodes, prior model predictions or organization text. Output includes explanation and one <answer>label</answer>.

Direct has a single inference stage and accepts one completed response. Transport failures may retry; a received but invalid response is recorded as failure without model-assisted repair. Artifacts and request attempts are preserved. Token totals cover recorded responses only.

These model-selected balanced development samples do not represent untouched benchmark test accuracy. Previous five-model comparisons use four frames.
