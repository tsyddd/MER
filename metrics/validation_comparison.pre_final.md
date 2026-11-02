# Validation comparison

MER2024: 40 samples, six classes. MELD: 40 samples, seven classes. Errors count as incorrect in ACC-all. These are model-selected development subsets, not untouched benchmark tests.

| Method | Frames | MER2024 | MELD | All80 | Completed |
|---|---:|---:|---:|---:|---:|
| Emotion-LLaMA | 4 | 82.50% (33/40) | 65.00% (26/40) | 73.75% (59/80) | 80/80 |
| AffectGPT | 4 | 67.50% (27/40) | 77.50% (31/40) | 72.50% (58/80) | 80/80 |
| AffectGPT-RL | 4 | 77.50% (31/40) | 37.50% (15/40) | 57.50% (46/80) | 80/80 |
| OPPO | 4 | 80.00% (32/40) | 55.00% (22/40) | 67.50% (54/80) | 80/80 |
| VidEmo-7B | 4 | 67.50% (27/40) | 70.00% (28/40) | 68.75% (55/80) | 80/80 |
| direct/omni | 8 | 85.00% (34/40) | 60.00% (24/40) | 72.50% (58/80) | 80/80 |
| ppct/omni | 8 | 75.00% (30/40) | 62.50% (25/40) | 68.75% (55/80) | 80/80 |
| ppct/gpt | 8 | 77.50% (31/40) | 77.50% (31/40) | 77.50% (62/80) | 80/80 |
| ppct/gemini | 8 | 75.00% (30/40) | 60.00% (24/40) | 67.50% (54/80) | 80/80 |

GPT uses eight frames and available subtitle without audio (endpoint rejects audio). Gemini and Omni use eight frames, original audio and available subtitle. All PPCT stages are model-specific; original five model answers and gold labels are never sent as inference context.
