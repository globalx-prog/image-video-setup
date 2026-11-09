#!/bin/bash
# ==============================================================================
# 🎬 1-Klick Testlauf: 3-Szenen Langfilm mit MiniMax H3 (15s)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "=================================================================="
echo " 🎬 Starte 3-Szenen Testlauf (15s Gesamtfilm mit Charakter-Konsistenz)"
echo "=================================================================="

# Aktiviere die ComfyUI Python-Umgebung
if [ -d "comfy_env" ]; then
    source comfy_env/bin/activate
fi

# Führe Pipeline aus
python3 scripts/auto_movie_maker.py \
    --story configs/story_3scenes_test.yaml \
    --character "ComfyUI/input/YOTTEA-KREA-PRO (21).png" \
    --output "output/test_movie_3scenes" \
    --width 864 \
    --height 480 \
    --duration 5.0 \
    "$@"

echo -e "\n✅ Fertig! Das Video liegt unter: output/test_movie_3scenes/gesamtfilm_15s.mp4"

