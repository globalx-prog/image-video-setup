#!/bin/bash
# ==============================================================================
# 🎬 run_krimi_intro.sh — 30s Film-Noir Krimi Intro (6 Szenen)
# ==============================================================================
# Vollautomatische Produktion eines 30-Sekunden Krimi-Serienintros
# mit nativer Stereotonspur, Charakter-Konsistenz und nahtlosen Übergängen.
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

STORY_FILE="configs/krimi_intro_30s.yaml"
OUTPUT_DIR="output/krimi_intro_30s"
DEFAULT_CHAR="ComfyUI/input/detective_portrait.png"
FALLBACK_CHAR="ComfyUI/input/YOTTEA-KREA-PRO (21).png"

# Prüfe Charakter-Bild
if [ -f "$DEFAULT_CHAR" ]; then
    CHAR_IMG="$DEFAULT_CHAR"
elif [ -f "$FALLBACK_CHAR" ]; then
    CHAR_IMG="$FALLBACK_CHAR"
    echo "[HINWEIS] Kein 'detective_portrait.png' gefunden — nutze vorhandenes Bild: $FALLBACK_CHAR"
    echo "          (Tipp: Lege dein eigenes Detektiv-Porträt unter 'ComfyUI/input/detective_portrait.png' ab)"
else
    # Finde erstes passendes PNG in ComfyUI/input
    CHAR_IMG=$(find ComfyUI/input -maxdepth 1 -name "*.png" | head -n 1)
fi

echo "=================================================================="
echo " 🎬 Starte 30s Film-Noir Krimi Intro Pipeline (6 Szenen à 5s)"
echo "=================================================================="
echo " Storyboard:      $STORY_FILE"
echo " Hauptfigur:      $CHAR_IMG"
echo " Ausgabepfad:     $OUTPUT_DIR"
echo " Zusätzliche Flags: $@"
echo "=================================================================="

# Aktiviere die ComfyUI Python-Umgebung
if [ -d "comfy_env" ]; then
    source comfy_env/bin/activate
fi

# Starte Pipeline
python3 scripts/auto_movie_maker.py \
    --story "$STORY_FILE" \
    --character "$CHAR_IMG" \
    --output "$OUTPUT_DIR" \
    --width 864 \
    --height 480 \
    --duration 5.0 \
    "$@"

echo ""
echo "=================================================================="
echo " ✅ 30s Krimi-Intro erfolgreich fertiggestellt!"
echo " 📁 Fertiger Film: $OUTPUT_DIR/gesamtfilm_30s.mp4"
echo "=================================================================="

