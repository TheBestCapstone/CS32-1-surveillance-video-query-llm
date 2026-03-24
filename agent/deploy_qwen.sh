#!/bin/bash

# Activate the conda environment
source /home/yangxp/anaconda3/bin/activate capstone

# Start the vLLM OpenAI-compatible server using HuggingFace
# You can adjust max-model-len based on your needs and VRAM. 8192 is a good default.
# The 5090 has 32GB VRAM, so we can use a decent max-model-len.
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 16384 \
    --limit-mm-per-prompt '{"image": 4}' \
    --trust-remote-code
