#!/bin/bash
# ==============================================================================
# 🚀 Wan 2.2 Image-to-Video Downloader (AMD Radeon PRO W7800 48 GB optimiert)
# Lädt die 2 DiT-Cores (High & Low Noise) und die 4-Step Turbo-LoRAs herunter.
# ==============================================================================

set -e

COMFY_DIR="/home/clemi/Projekte/LLM/image-video-setup/ComfyUI"
DIFF_DIR="$COMFY_DIR/models/diffusion_models"
LORA_DIR="$COMFY_DIR/models/loras"
ENC_DIR="$COMFY_DIR/models/text_encoders"
VAE_DIR="$COMFY_DIR/models/vae"
WORKFLOW_DIR="$COMFY_DIR/user/default/workflows"

mkdir -p "$DIFF_DIR" "$LORA_DIR" "$ENC_DIR" "$VAE_DIR" "$WORKFLOW_DIR"

echo "=================================================================="
echo " 🎬 Wan 2.2 Setup für ComfyUI (14B Dual-Stage DiT + 4-Step LoRA)"
echo "=================================================================="

# Basis-URLs (Hugging Face Repackaged von Comfy-Org)
HF_BASE="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files"

# 1. Vorhandene Abhängigkeiten prüfen
echo "--> [1/4] Prüfe vorhandene Basis-Komponenten..."
if [ -f "$ENC_DIR/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
    echo "  ✅ Text-Encoder (UMT5-XXL FP8) bereits vorhanden: $ENC_DIR/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
else
    echo "  ⚠️ Text-Encoder fehlt! Lade herunter..."
    wget -c --progress=dot:giga -O "$ENC_DIR/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
      "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
fi

if [ -f "$VAE_DIR/wan_2.1_vae.safetensors" ]; then
    echo "  ✅ VAE (wan_2.1_vae) bereits vorhanden: $VAE_DIR/wan_2.1_vae.safetensors"
else
    echo "  ⚠️ VAE fehlt! Lade herunter..."
    wget -c --progress=dot:giga -O "$VAE_DIR/wan_2.1_vae.safetensors" \
      "$HF_BASE/vae/wan_2.1_vae.safetensors"
fi

echo ""
echo "--> [2/4] Lade Diffusion Models (High-Noise & Low-Noise) herunter..."
# High-Noise DiT (~13.3 GB)
if [ -f "$DIFF_DIR/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" ]; then
    echo "  ✅ High-Noise DiT bereits vorhanden!"
else
    echo "  ⬇️ Lade wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors (~13.3 GB)..."
    wget -c --progress=dot:giga -O "$DIFF_DIR/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
      "$HF_BASE/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
fi

# Low-Noise DiT (~13.3 GB)
if [ -f "$DIFF_DIR/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" ]; then
    echo "  ✅ Low-Noise DiT bereits vorhanden!"
else
    echo "  ⬇️ Lade wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors (~13.3 GB)..."
    wget -c --progress=dot:giga -O "$DIFF_DIR/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
      "$HF_BASE/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
fi

echo ""
echo "--> [3/4] Lade 4-Step Turbo-LoRAs herunter..."
# LoRA High-Noise (~1.14 GB)
if [ -f "$LORA_DIR/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" ]; then
    echo "  ✅ LoRA High-Noise bereits vorhanden!"
else
    echo "  ⬇️ Lade wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors (~1.14 GB)..."
    wget -c --progress=dot:giga -O "$LORA_DIR/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" \
      "$HF_BASE/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
fi

# LoRA Low-Noise (~1.14 GB)
if [ -f "$LORA_DIR/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" ]; then
    echo "  ✅ LoRA Low-Noise bereits vorhanden!"
else
    echo "  ⬇️ Lade wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors (~1.14 GB)..."
    wget -c --progress=dot:giga -O "$LORA_DIR/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" \
      "$HF_BASE/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
fi

echo ""
echo "--> [4/4] Kopiere offiziellen Wan 2.2 I2V Workflow..."
TEMPLATE_SRC="/home/clemi/Projekte/LLM/image-video-setup/comfy_env/lib/python3.12/site-packages/comfyui_workflow_templates_json/templates/video_wan2_2_14B_i2v.json"
if [ -f "$TEMPLATE_SRC" ]; then
    cp "$TEMPLATE_SRC" "$WORKFLOW_DIR/wan2.2_i2v.json"
    echo "  ✅ Workflow bereitgestellt unter: ComfyUI/user/default/workflows/wan2.2_i2v.json"
fi

echo ""
echo "=================================================================="
echo " 🎉 Fertig! Alle Wan 2.2 Modelle sind vollständig installiert."
echo " 👉 Du findest den Workflow in ComfyUI unter:"
echo "    Workflows -> wan2.2_i2v"
echo "=================================================================="

