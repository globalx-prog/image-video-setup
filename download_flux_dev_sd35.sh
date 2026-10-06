#!/bin/bash
set -e
CKPT_DIR="/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints"

echo "=== [1/2] FLUX.1 [dev] FP8 (~17.2GB) ==="
wget -c --progress=dot:giga -O "$CKPT_DIR/flux1-dev-fp8.safetensors" \
  "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors"

echo "=== [2/2] Stable Diffusion 3.5 Large FP8 (~14.9GB) ==="
wget -c --progress=dot:giga -O "$CKPT_DIR/sd3.5_large_fp8_scaled.safetensors" \
  "https://huggingface.co/Comfy-Org/stable-diffusion-3.5-fp8/resolve/main/sd3.5_large_fp8_scaled.safetensors"

echo "=== Downloads fertig! Aktualisiere ComfyUI... ==="
curl -s http://127.0.0.1:8188/refresh || true
