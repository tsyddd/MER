# Frozen Gemini graphs + three independent experts

Each provider: frozen Gemini graph -> own organization -> graph / audio+subtitle /8-image experts -> text-only summary. Same fixed80 development samples, no prompt optimization.
GPT audio+subtitle branch receives subtitle only; graph branch indirectly receives Gemini audio-derived observations. Summary never receives raw media. Each expert is the same requested model as its summary, not cross-model voting.

| Model | MER2024 | MELD | All80 | Audited | Responses | Total tokens | Successful stage seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt | 60.00% (24/40) | 52.50% (21/40) | 56.25% (45/80) | 80/80 | 400 | 608328 | 6223.2 |
| gemini | 77.50% (31/40) | 55.00% (22/40) | 66.25% (53/80) | 80/80 | 402 | 1239652 | 2827.9 |
| omni | pending | pending | pending | 70/80 | 517 | 633405 | 3048.0 |

Prior baseline/PPCT comparison: metrics/validation_comparison.md. Frozen graph hashes: data/gemini_graph_three_experts_v1/manifest.json.
Graph integrity, source identity, 8-frame hashes, stage outputs, source isolation, answer wrapping, label space, request payload leakage and summary dependencies audited per unique sample ID. This does not verify semantic truth of every observation.
Recorded usage includes persisted responses for this experiment, excluding source-graph generation, external connection probes and failed network requests with no response. Successful stage time is a sum, not end-to-end wall time. Candidate/provider identity is as reported by the configured service.
