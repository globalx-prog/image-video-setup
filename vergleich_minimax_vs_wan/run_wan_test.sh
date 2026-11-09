#!/bin/bash
# ==============================================================================
# 🎬 1-Klick Testlauf: 3-Szenen Film mit WAN 2.2 (15s)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "=================================================================="
echo " 🎬 Starte WAN 2.2 Testlauf (15s Gesamtfilm im 4-Step Turbo Modus)"
echo "=================================================================="

if [ -d "comfy_env" ]; then
    source comfy_env/bin/activate
fi

python3 vergleich_minimax_vs_wan/wan_movie_maker.py \
    --story vergleich_minimax_vs_wan/wan_story_test.yaml \
    --character "ComfyUI/input/YOTTEA-KREA-PRO (21).png" \
    --output "output/wan_test_movie" \
    --steps 4 \
    "$@"

echo -e "\n✅ Fertig! Das WAN 2.2 Video liegt unter: output/wan_test_movie/wan_gesamtfilm_15s.mp4"

