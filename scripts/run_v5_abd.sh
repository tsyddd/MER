#!/bin/bash
# Server driver: v5 methods A, B1, D on the v4 disagreement samples, Gemini and GPT in parallel, methods one after another
# per provider (4 samples in parallel per method). B0 needs no model call and is run separately.
cd "$(dirname "$0")/.." || exit 1
for p in gemini gpt; do
  (
    for m in D A B1; do
      .venv/bin/python versions/v5/pipeline.py run --provider "$p" --method "$m" --workers 4 > "logs/v5_${m}_${p}.log" 2>&1
      echo "$p $m exit $?" >> logs/run_v5_abd.log
    done
  ) &
done
wait
echo "all done" >> logs/run_v5_abd.log
