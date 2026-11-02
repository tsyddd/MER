#!/usr/bin/env bash
set -euo pipefail
cd /media/liang/12T/han/open_source_generated/PPCT_emotion_training_free
export CUDA_VISIBLE_DEVICES=0,1,2,3
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_ATTENTION_BACKEND=FLASH_ATTN
export OMP_NUM_THREADS=4
export TZ=Asia/Shanghai
exec .venv/bin/python -u -m vllm.entrypoints.openai.api_server \
  --model "$PWD/models/Qwen3-Omni-30B-A3B-Thinking" \
  --served-model-name omni30b-thinking --host 127.0.0.1 --port 18030 \
  --tensor-parallel-size 4 --dtype bfloat16 --max-model-len 16384 \
  --max-num-seqs 1 --gpu-memory-utilization 0.90 --enforce-eager \
  --skip-mm-profiling --kv-cache-memory-bytes 1073741824 \
  --max-num-batched-tokens 4096 --disable-custom-all-reduce \
  --limit-mm-per-prompt '{"image":8,"audio":1,"video":0}' \
  --allowed-local-media-path "$PWD/data" --reasoning-parser qwen3
