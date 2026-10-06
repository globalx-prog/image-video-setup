#!/bin/bash
set -e
BASE="/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models"

echo "=== [1/3] Wan 2.1 VAE (~254MB) ==="
wget -c --progress=dot:giga -O "$BASE/vae/wan_2.1_vae.safetensors" \
  "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors"

echo "=== [2/3] Wan 2.1 Text Encoder UMT5-XXL FP8 (~6.7GB) ==="
wget -c --progress=dot:giga -O "$BASE/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
  "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

echo "=== [3/3] Wan 2.1 T2V 14B BF16 Diffusion Model (~28.5GB) ==="
wget -c --progress=dot:giga -O "$BASE/diffusion_models/wan2.1_t2v_14B_bf16.safetensors" \
  "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_bf16.safetensors"

echo "=== Wan 2.1 Download abgeschlossen! Aktualisiere ComfyUI... ==="
curl -s http://127.0.0.1:8188/refresh || true
