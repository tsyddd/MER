# Fixed validation comparison

| Model / method | Frames | MER2024 | MELD | All80 | Valid |
|---|---:|---:|---:|---:|---:|
| Emotion-LLaMA | 4 | 82.50% (33/40) | 65.00% (26/40) | 73.75% (59/80) | 80/80 |
| AffectGPT | 4 | 67.50% (27/40) | 77.50% (31/40) | 72.50% (58/80) | 80/80 |
| AffectGPT-RL | 4 | 77.50% (31/40) | 37.50% (15/40) | 57.50% (46/80) | 80/80 |
| OPPO | 4 | 80.00% (32/40) | 55.00% (22/40) | 67.50% (54/80) | 80/80 |
| VidEmo-7B | 4 | 67.50% (27/40) | 70.00% (28/40) | 68.75% (55/80) | 80/80 |
| Qwen3-Omni-30B-A3B-Instruct / direct | 8 | 85.00% (34/40) | 60.00% (24/40) | 72.50% (58/80) | 80/80 |
| Qwen3-Omni-30B-A3B-Instruct / ppct | 8 | 75.00% (30/40) | 62.50% (25/40) | 68.75% (55/80) | 80/80 |
| gpt / direct | 8 | 60.00% (24/40) | 70.00% (28/40) | 65.00% (52/80) | 80/80 |
| gpt / ppct | 8 | 77.50% (31/40) | 77.50% (31/40) | 77.50% (62/80) | 80/80 |
| gemini / direct | 8 | 82.50% (33/40) | 67.50% (27/40) | 75.00% (60/80) | 80/80 |
| gemini / ppct | 8 | 75.00% (30/40) | 60.00% (24/40) | 67.50% (54/80) | 80/80 |

All six new-method groups audited: True. Pending groups have no final ACC.

| Method | Valid / expected | Incomplete or invalid | Recorded responses | Prompt tokens | Completion tokens | Total tokens | Successful stage time (seconds) |
|---|---:|---:|---:|---:|---:|---:|---:|
| direct/omni | 80/80 | 0 | 80 | 104117 | 4494 | 108611 | 438.5 |
| ppct/omni | 80/80 | 0 | 406 | 796758 | 150805 | 947563 | 11398.2 |
| direct/gpt | 80/80 | 0 | 80 | 136255 | 11854 | 148109 | 2161.7 |
| ppct/gpt | 80/80 | 0 | 406 | 884334 | 168287 | 1052621 | 6442.3 |
| direct/gemini | 80/80 | 0 | 80 | 734048 | 25937 | 759985 | 667.0 |
| ppct/gemini | 80/80 | 0 | 416 | 3416685 | 348207 | 3764892 | 4054.9 |

GPT uses frames and available subtitle; Gemini/Omni also receive original audio. Direct inference has one stage and no graph/organization context; PPCT has five stages including a program-built graph. Output includes evidence explanation and exactly one <answer>label</answer>.

Omni is the existing Instruct checkpoint served on dashan; Thinking is retained on liang but unused in this evaluation.

Limits:
- Balanced development subset selected using prior model correctness, not untouched benchmark accuracy.
- Four-frame prior models versus eight-frame new methods are not a controlled frame-matched comparison.
- Audit verifies flow/format and input protocol, not factual correctness of each explanation.
- Recorded usage may omit overwritten historical retries, network failures and separate probes; summed successful stage times are not end-to-end wall time.
- Omni permits logged structural normalization/deletion of invalid edges and recovery of complete typed nodes from truncated responses, discarding incomplete tails and exact repeated content; GPT/Gemini use strict validation with generated repair feedback.
