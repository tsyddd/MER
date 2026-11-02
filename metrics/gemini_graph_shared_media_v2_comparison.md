# Frozen Gemini graphs + three independent experts

V2: frozen Gemini graph -> own organization -> three independent role-specialized experts with shared8 images/audio/subtitles -> raw-media summary without graph. Four rubrics per role, one manual reflect on8 prior outputs (6 unique clips); these80 are reused development data, not held-out results.
GPT audio+subtitle branch receives subtitle only; graph branch indirectly receives Gemini audio-derived observations. Summary receives raw media but no graph/organization; only graph expert gets graph/organization. Each expert is the same requested model as its summary, not cross-model voting.

| Model | MER2024 | MELD | All80 | Audited | Responses | Total tokens | Successful stage seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt | 60.00% (24/40) | 67.50% (27/40) | 63.75% (51/80) | 80/80 | 408 | 1292379 | 10217.9 |
| gemini | 77.50% (31/40) | 62.50% (25/40) | 70.00% (56/80) | 80/80 | 405 | 3834329 | 4895.3 |
| omni | pending | pending | pending | 76/80 | 429 | 1037398 | 11847.3 |

Prior baseline/PPCT comparison: metrics/validation_comparison.md. Frozen graph hashes: data/gemini_graph_three_experts_v1/manifest.json.
Graph integrity,8-frame hashes, shared media per role, exclusive graph access, evidence reference validity, answer wrapping, label space, no-gold payload and summary dependencies audited per unique sample ID. This does not verify semantic truth of every observation.
Recorded usage includes persisted responses for this experiment, excluding source-graph generation, external connection probes and failed network requests with no response. Successful stage time is a sum, not end-to-end wall time. Candidate/provider identity is as reported by the configured service.
