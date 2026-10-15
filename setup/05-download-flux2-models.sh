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

# Download-Funktion mit automatischer Größenprüfung und Wiederaufnahme (Resume)
download_or_resume() {
    local target="$1"
    local url="$2"
    local expected_size="$3"
    local name="$4"

    local current_size=0
    if [ -f "$target" ]; then
        current_size=$(stat -c%s "$target" 2>/dev/null || echo 0)
    fi

    if [ "$current_size" -ge "$expected_size" ]; then
        echo "  ✅ $name bereits vollständig vorhanden ($(numfmt --to=iec-i --suffix=B $current_size))"
        return 0
    fi

    if [ "$current_size" -gt 0 ]; then
        local percent=$(( 100 * current_size / expected_size ))
        echo "  ⚠️ $name ist unvollständig ($percent% geladen: $(numfmt --to=iec-i --suffix=B $current_size) / $(numfmt --to=iec-i --suffix=B $expected_size))."
        echo "  🔄 Setze Download nahtlos an der Abbruchstelle fort..."
    else
        echo "  ⬇️ Lade $name herunter ($(numfmt --to=iec-i --suffix=B $expected_size))..."
    fi

    if command -v curl >/dev/null 2>&1; then
        curl -C - -L --progress-bar -o "$target" "$url"
    else
        wget -c --progress=dot:giga -O "$target" "$url"
    fi

    local final_size=$(stat -c%s "$target" 2>/dev/null || echo 0)
    if [ "$final_size" -ge "$expected_size" ]; then
        echo "  ✅ $name erfolgreich vollständig heruntergeladen ($(numfmt --to=iec-i --suffix=B $final_size))."
    else
        echo "  ❌ Fehler: $name ist noch unvollständig ($final_size / $expected_size Bytes)."
        return 1
    fi
}

# ------------------------------------------------------------------------------
# 1. VAE herunterladen (flux2-vae.safetensors)
# ------------------------------------------------------------------------------
echo "--> [1/4] Prüfe FLUX.2 VAE..."
download_or_resume \
    "$VAE_DIR/flux2-vae.safetensors" \
    "$HF_BASE/vae/flux2-vae.safetensors" \
    335856158 \
    "flux2-vae.safetensors"

# ------------------------------------------------------------------------------
# 2. Text Encoder herunterladen (Mistral-3 Small)
# ------------------------------------------------------------------------------
echo ""
echo "--> [2/4] Prüfe FLUX.2 Text-Encoder (Mistral-3 Small)..."
if [ "$USE_BF16" = true ]; then
    download_or_resume \
        "$ENC_DIR/mistral_3_small_flux2_bf16.safetensors" \
        "$HF_BASE/text_encoders/mistral_3_small_flux2_bf16.safetensors" \
        35584897447 \
        "mistral_3_small_flux2_bf16.safetensors"
else
    download_or_resume \
        "$ENC_DIR/mistral_3_small_flux2_fp8.safetensors" \
        "$HF_BASE/text_encoders/mistral_3_small_flux2_fp8.safetensors" \
        18034640095 \
        "mistral_3_small_flux2_fp8.safetensors"
fi

# ------------------------------------------------------------------------------
# 3. Diffusion Transformer (DiT) herunterladen
# ------------------------------------------------------------------------------
echo ""
echo "--> [3/4] Prüfe FLUX.2 [dev] Diffusion Model..."
# Comfy-Org stellt das offizielle FLUX.2 Dev DiT in FP8-Mixed (~33 GiB / 35.5 GB) bereit
download_or_resume \
    "$DIFF_DIR/flux2_dev_fp8mixed.safetensors" \
    "$HF_BASE/diffusion_models/flux2_dev_fp8mixed.safetensors" \
    35455599592 \
    "flux2_dev_fp8mixed.safetensors"

# ------------------------------------------------------------------------------
# 4. Turbo-LoRA herunterladen (optional 8-Step Schnellmodus)
# ------------------------------------------------------------------------------
LORA_DIR="$COMFY_DIR/models/loras"
mkdir -p "$LORA_DIR"
echo ""
echo "--> [4/4] Prüfe FLUX.2 Turbo LoRA (8 Steps Speedup)..."
download_or_resume \
    "$LORA_DIR/Flux_2-Turbo-LoRA_comfyui.safetensors" \
    "$HF_BASE/loras/Flux_2-Turbo-LoRA_comfyui.safetensors" \
    2760814880 \
    "Flux_2-Turbo-LoRA_comfyui.safetensors"

# ------------------------------------------------------------------------------
# 5. Optional: Template-Workflow bereitstellen
# ------------------------------------------------------------------------------
echo ""
TEMPLATE_SRC="/home/clemi/Projekte/LLM/image-video-setup/comfy_env/lib/python3.12/site-packages/comfyui_workflow_templates_json/templates/image_flux2_dev.json"
if [ -f "$TEMPLATE_SRC" ]; then
    mkdir -p "$WORKFLOW_DIR/flux2"
    cp "$TEMPLATE_SRC" "$WORKFLOW_DIR/flux2/flux2_dev_template.json"
    echo "  ✅ Offizieller Workflow bereitgestellt: ComfyUI/user/default/workflows/flux2/flux2_dev_template.json"
fi

echo ""
echo "=================================================================="
echo " 🎉 Fertig! Alle FLUX.2 [dev] Komponenten sind einsatzbereit."
echo ""
echo " Gespeichert in:"
echo " • DiT:          $DIFF_DIR/flux2_dev_fp8mixed.safetensors"
echo " • Text-Encoder: $ENC_DIR"
echo " • VAE:          $VAE_DIR/flux2-vae.safetensors"
echo " • Turbo-LoRA:   $LORA_DIR/Flux_2-Turbo-LoRA_comfyui.safetensors"
echo "=================================================================="

