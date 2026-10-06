#!/bin/bash
set -e

BASE="/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models"
INPUT_DIR="/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/input"

mkdir -p "$BASE/vae"
mkdir -p "$BASE/text_encoders"
mkdir -p "$BASE/diffusion_models"
mkdir -p "$BASE/loras"
mkdir -p "$INPUT_DIR"

echo "=========================================================="
echo " Starting Download of MiniMax-H3 (AMD ROCm / HIP Edition)"
echo " Total size: ~50 GB | Destination: $BASE"
echo "=========================================================="

echo ""
echo "=== [1/6] MiniMax Video VAE (int8_convrot, ~2.6 GB) ==="
wget -c --progress=dot:giga -O "$BASE/vae/minimax_h3_video_vae_int8_convrot.safetensors" \
  "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot.safetensors"

echo ""
echo "=== [2/6] MiniMax Audio VAE (fp32, ~580 MB) ==="
wget -c --progress=dot:giga -O "$BASE/vae/minimax_h3_audio_vae_fp32.safetensors" \
  "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors"

echo ""
echo "=== [3/6] Qwen3-VL 32B Text Encoder (AMD-native int8_convrot, ~25.3 GB) ==="
wget -c --progress=dot:giga -O "$BASE/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors" \
  "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors"

# Symlink: If any legacy workflow expects the NVFP4 filename, point it to the AMD int8 file
echo "Creating compatibility symlink for legacy NVFP4 references..."
ln -sf "qwen3vl_32b_minimax_h3_int8_convrot.safetensors" "$BASE/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"

echo ""
echo "=== [4/6] MiniMax-H3 FL2VA Diffusion Core (pruned int8_convrot, ~19.5 GB) ==="
wget -c --progress=dot:giga -O "$BASE/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors" \
  "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"

echo ""
echo "=== [5/6] MiniMax-H3 Turbo LoRA (8-Step Fast Sampling, ~1.8 GB) ==="
wget -c --progress=dot:giga -O "$BASE/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors" \
  "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"

echo ""
echo "=== [6/6] Example Workflow Input Image ==="
wget -c -O "$INPUT_DIR/transparent_rgb_gaming_mouse.png" \
  "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/input/transparent_rgb_gaming_mouse.png"

echo ""
echo "=== MiniMax-H3 Download completed successfully! Refreshing ComfyUI... ==="
curl -s http://127.0.0.1:8188/refresh || true
echo "Ready!"

