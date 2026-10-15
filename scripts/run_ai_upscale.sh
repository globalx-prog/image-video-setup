#!/bin/bash
# ==============================================================================
# 🎬 run_ai_upscale.sh — Standalone KI-Video Super-Resolution Runner (AMD ROCm)
# ==============================================================================
# Skaliert generierte Videos (z. B. 864x480) mittels Real-ESRGAN neuronal
# auf kristallklares 1080p Full HD oder 4K hoch.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Aktiviere die Umgebung
if [ -d "comfy_env" ]; then
    source comfy_env/bin/activate
fi

# Performance-Tuning für AMD ROCm 6.4 & RDNA3
export TORCH_BLAS_PREFER_HIPBLASLT=1
export AMD_SERIALIZE_KERNEL=0
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Starte Python Upscaler
python3 scripts/ai_video_upscaler.py "$@"

