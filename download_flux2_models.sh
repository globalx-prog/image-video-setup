#!/bin/bash
# ==============================================================================
# 🚀 FLUX.2 [dev] Downloader für ComfyUI (AMD Radeon PRO W7800 48 GB optimiert)
# Lädt die offiziellen Repackaged-Komponenten von Comfy-Org herunter:
# - Diffusion Transformer (DiT): FLUX.2 Dev (FP8-Mixed / BF16)
# - Text-Encoder: Mistral-3 Small FLUX.2
# - VAE: FLUX.2 VAE
# ==============================================================================

set -e

COMFY_DIR="/home/clemi/Projekte/LLM/image-video-setup/ComfyUI"
DIFF_DIR="$COMFY_DIR/models/diffusion_models"
ENC_DIR="$COMFY_DIR/models/text_encoders"
VAE_DIR="$COMFY_DIR/models/vae"
WORKFLOW_DIR="$COMFY_DIR/user/default/workflows"

mkdir -p "$DIFF_DIR" "$ENC_DIR" "$VAE_DIR" "$WORKFLOW_DIR"

# Hugging Face Basis-URL (Comfy-Org Repackaged)
HF_BASE="https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files"

echo "=================================================================="
echo " 🎨 FLUX.2 [dev] Setup für ComfyUI (AMD ROCm 6.4 / W7800 48 GB)"
echo "=================================================================="

# Auswahl-Prüfung: Standard ist FP8-Mixed (optimal für 48 GB), optional BF16
USE_BF16=false
if [ "$1" == "--bf16" ]; then
    USE_BF16=true
    echo " ⚙️ Modus: BF16 (Vollpräzision / Unkomprimiert ~32 GB DiT)"
else
    echo " ⚙️ Modus: FP8-Mixed (Empfohlen für Highspeed & Spitzenqualität)"
    echo "    (Hinweis: Für unkomprimiertes BF16 starte: ./download_flux2_models.sh --bf16)"
fi
echo "=================================================================="
echo ""

# ------------------------------------------------------------------------------
# 1. VAE herunterladen
# ------------------------------------------------------------------------------
echo "--> [1/3] Prüfe FLUX.2 VAE..."
if [ -f "$VAE_DIR/flux2-vae.safetensors" ]; then
    echo "  ✅ VAE bereits vorhanden: $VAE_DIR/flux2-vae.safetensors"
else
    echo "  ⬇️ Lade flux2-vae.safetensors herunter (~330 MB)..."
    wget -c --progress=dot:giga -O "$VAE_DIR/flux2-vae.safetensors" \
      "$HF_BASE/vae/flux2-vae.safetensors"
fi

# ------------------------------------------------------------------------------
# 2. Text Encoder herunterladen (Mistral-3 Small)
# ------------------------------------------------------------------------------
echo ""
echo "--> [2/3] Prüfe FLUX.2 Text-Encoder (Mistral-3 Small)..."

if [ "$USE_BF16" = true ]; then
    ENC_FILE="mistral_3_small_flux2_bf16.safetensors"
    ENC_URL="$HF_BASE/text_encoders/mistral_3_small_flux2_bf16.safetensors"
else
    ENC_FILE="mistral_3_small_flux2_fp8.safetensors"
    ENC_URL="$HF_BASE/text_encoders/mistral_3_small_flux2_fp8.safetensors"
fi

if [ -f "$ENC_DIR/$ENC_FILE" ]; then
    echo "  ✅ Text-Encoder bereits vorhanden: $ENC_DIR/$ENC_FILE"
else
    echo "  ⬇️ Lade $ENC_FILE herunter (~7.5 GB)..."
    wget -c --progress=dot:giga -O "$ENC_DIR/$ENC_FILE" "$ENC_URL"
fi

# ------------------------------------------------------------------------------
# 3. Diffusion Model (DiT) herunterladen
# ------------------------------------------------------------------------------
echo ""
echo "--> [3/3] Prüfe FLUX.2 [dev] Diffusion Model..."

if [ "$USE_BF16" = true ]; then
    DIT_FILE="flux2_dev.safetensors"
    DIT_URL="$HF_BASE/diffusion_models/flux2_dev.safetensors"
    DIT_SIZE="~32 GB"
else
    DIT_FILE="flux2_dev_fp8mixed.safetensors"
    DIT_URL="$HF_BASE/diffusion_models/flux2_dev_fp8mixed.safetensors"
    DIT_SIZE="~17.5 GB"
fi

if [ -f "$DIFF_DIR/$DIT_FILE" ]; then
    echo "  ✅ Diffusion Model bereits vorhanden: $DIFF_DIR/$DIT_FILE"
else
    echo "  ⬇️ Lade $DIT_FILE herunter ($DIT_SIZE)..."
    wget -c --progress=dot:giga -O "$DIFF_DIR/$DIT_FILE" "$DIT_URL"
fi

# ------------------------------------------------------------------------------
# 4. Optional: Template-Workflow bereitstellen
# ------------------------------------------------------------------------------
echo ""
TEMPLATE_SRC="/home/clemi/Projekte/LLM/image-video-setup/comfy_env/lib/python3.12/site-packages/comfyui_workflow_templates_json/templates/image_flux2_dev.json"
if [ -f "$TEMPLATE_SRC" ]; then
    cp "$TEMPLATE_SRC" "$WORKFLOW_DIR/flux2_dev.json"
    echo "  ✅ Offizieller Workflow bereitgestellt: ComfyUI/user/default/workflows/flux2_dev.json"
fi

echo ""
echo "=================================================================="
echo " 🎉 Fertig! Alle FLUX.2 [dev] Komponenten sind einsatzbereit."
echo ""
echo " Gespeichert in:"
echo " • DiT:          $DIFF_DIR/$DIT_FILE"
echo " • Text-Encoder: $ENC_DIR/$ENC_FILE"
echo " • VAE:          $VAE_DIR/flux2-vae.safetensors"
echo "=================================================================="

