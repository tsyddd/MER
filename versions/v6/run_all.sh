#!/bin/bash
# Server driver of the R2-MAD (v6) pipeline after the pool screening: captions of the training samples -> training debates (memory build) for
# Gemini and GPT in parallel -> embeddings -> test-set captions -> test variants n0 (control) / n1 / n2 / n3 per provider -> report.
# Waits for versions/v6/pool.py to finish first. Request-level concurrency (Gemini 4, GPT 2) is enforced inside versions/v6/common.py
# across all processes, so the stages may overlap. Every stage is cached and resumable.
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python
echo "$(date '+%F %T') waiting for pool screening" >> logs/v6_run_all.log
while pgrep -f "versions/v6/pool.py run" > /dev/null; do sleep 120; done
if [ ! -f outputs/v6_rmad/pool/selection.json ]; then echo "$(date '+%F %T') pool selection.json missing, stop" >> logs/v6_run_all.log; exit 1; fi
echo "$(date '+%F %T') pool done" >> logs/v6_run_all.log
$PY versions/v6/captions.py run --set train --workers 6 > logs/v6_caption_train.log 2>&1
echo "$(date '+%F %T') train captions exit $?" >> logs/v6_run_all.log
$PY versions/v6/captions.py run --set test --workers 6 > logs/v6_caption_test.log 2>&1
for p in gemini gpt; do
  $PY versions/v6/build_memory.py debates --provider $p --workers 6 > logs/v6_build_$p.log 2>&1 &
done
wait
echo "$(date '+%F %T') training debates exit $?" >> logs/v6_run_all.log
rm -rf outputs/v6_rmad/memory
for p in gemini gpt; do
  CUDA_VISIBLE_DEVICES=1 $PY versions/v6/build_memory.py embed --provider $p > logs/v6_embed_$p.log 2>&1
done
echo "$(date '+%F %T') embeddings exit $?" >> logs/v6_run_all.log
for p in gemini gpt; do
  (
    for v in n0 n1 n2 n3; do
      CUDA_VISIBLE_DEVICES=1 $PY versions/v6/run_rmad.py run --provider $p --variant $v --workers 6 > logs/v6_test_${p}_$v.log 2>&1
      echo "$(date '+%F %T') test $p $v exit $?" >> logs/v6_run_all.log
    done
  ) &
done
wait
$PY versions/v6/run_rmad.py report > logs/v6_report.log 2>&1
echo "$(date '+%F %T') all done" >> logs/v6_run_all.log
