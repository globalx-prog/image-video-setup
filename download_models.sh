#!/bin/bash
set -e
cd /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints

echo "=== [1/4] FLUX.1 Schnell FP8 (~17GB) fortsetzen/laden ==="
wget -c --progress=dot:giga -O flux1-schnell-fp8.safetensors "https://huggingface.co/Comfy-Org/flux1-schnell/resolve/main/flux1-schnell-fp8.safetensors"

echo "=== [2/4] LTX-Video 2B (~5.3GB) fortsetzen/laden ==="
wget -c --progress=dot:giga -O ltx-video-2b-v0.9.1.safetensors "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.1.safetensors"

echo "=== [3/4] SDXL Base 1.0 (~6.9GB) laden ==="
wget -c --progress=dot:giga -O sd_xl_base_1.0.safetensors "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"

echo "=== [4/4] Wan 2.1 1.3B Video (~3.2GB) laden ==="
wget -c --progress=dot:giga -O wan2.1_t2v_1.3B_fp16.safetensors "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_T2V_1.3B_fp16.safetensors" || true

echo "=== Alle Downloads abgeschlossen! Aktualisiere ComfyUI... ==="
curl -s http://127.0.0.1:8188/refresh || true
