# Fixed Gemini graph / independent experts evaluation

Experiment: `gemini_graph_three_experts_v1`. Fixed validation80 (MER2024/MELD40 each).
No prompt/skill optimization and no graph regeneration. Original evaluation outputs stay intact.

For each provider (GPT, Gemini, Omni Instruct):

1. Load the same SHA-256 verified Gemini graph for this sample.
2. That provider writes its own organization text, from graph+target metadata only.
3. That provider runs three independent experts:
   - `graph`: graph+organization, no raw media/subtitle file;
   - `audio_subtitle`: raw audio+available subtitle; GPT receives subtitle only;
   - `image`:8 ordered images+target metadata, no audio/subtitle text/graph/organization.
     Any readable text within the image is inherently visible and is not removed.
4. The same provider runs a text-only summary using the three expert outputs.
   It receives no raw media, graph or organization separately. It weighs evidence,
   not just label votes. Same-source evidence repeated by experts is not independent.
5. Save the explanation and one `<answer>label</answer>` result. Ground truth is added
   to the saved result only after inference, for offline scoring.

GPT indirectly receives Gemini audio-derived evidence through the graph branch.
This is a teacher-graph-assisted comparison, not equal raw modalities across models.
All providers use their own organization, experts and summary. Source graph is the
only cross-model artifact. The Gemini service identity is provider-reported.

## Files and operation

- Prompts: `frozen_graph_expert_prompts.py`.
- Pipeline, resumable stages, audit and controller: `frozen_graph_experts.py`.
- Frozen graph copies/hashes: `data/gemini_graph_three_experts_v1/manifest.json`.
- Outputs: `outputs/gemini_graph_three_experts_v1/{provider}/{dataset}/{sample_id}/`.
- Every stage has request, raw response, parsed JSON and signature/usage cache files.
- Status: `outputs/gemini_graph_three_experts_v1/controller_status.json`.
- Log: `logs/gemini_graph_three_experts_v1_controller.log` and provider job logs.
- Full per-sample audit: `metrics/gemini_graph_three_experts_v1_audit.json`.
- Scores/usage: `metrics/gemini_graph_three_experts_v1_comparison.md`.
- Prior scores: `metrics/validation_comparison.md`.

From the liang project directory:

```bash
.venv/bin/python frozen_graph_experts.py --self-test
.venv/bin/python frozen_graph_experts.py --audit
```

The controller runs two cross-dataset smoke samples per provider before its full80
job. Smoke successes are reused. It retries a failed pass at most once, skipping
successful samples and signature-matched completed stages. Do not run duplicate
controllers/workers; check PID, locks and logs first. A completed smoke is not80.
The report only gives final All80 ACC after all80 pass the stage/protocol audit.
The audit does not establish semantic correctness of every observation/reason.

The vLLM server stays running after the controller finishes. Training320 is not
included in this evaluation, and no API calls are made by `--audit`.
