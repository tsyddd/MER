#!/bin/bash
# Server driver: (1) Gemini graphs for the 320 train samples, (2) v4 pipeline for Gemini and GPT on all 400 samples
# (validation 80 results are cached and skipped). Concurrency: 4 samples in parallel per provider.
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python scripts/gen_train_graphs.py --workers 4 > logs/gen_train_graphs.log 2>&1
echo "graphs done: exit $?" >> logs/run_v4_400.log
for p in gemini gpt; do
  .venv/bin/python versions/v4/pipeline.py run --provider "$p" --workers 4 > "logs/reflect_debate_v4_${p}_400.log" 2>&1 &
done
wait
echo "v4 runs done" >> logs/run_v4_400.log
