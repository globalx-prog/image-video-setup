#!/bin/bash
# ==============================================================================
# 🎬 run_1min_movie.sh — 1-Minuten 2-Personen High-Detail Thriller (12 Szenen)
# ==============================================================================
# Vollautomatische Produktion eines 60-Sekunden High-Detail Neo-Noir Thrillers
# mit 2 konsistenten Hauptcharakteren (<Picture 1> & <Picture 2>),
# nativer Stereo-Soundkulisse und nahtlosem Ref2V / I2V-Schnitt.
#
# Enthält:
# - Interaktive Abfrage für Lüfter-Modus, Auflösung (MP) und KI-Upscaling
# - Automatische W7800 Blower-Regulierung mit Fallback auf vBIOS bei Skriptende
# - Durchgängige KI-Upscaling Post-Flight Pipeline (Real-ESRGAN auf 1080p)
# - Automatische Speicher- und Swap-Bereinigung gegen Desktop-Stocken
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

STORY_FILE="configs/krimi_story_1min_kino_flow.yaml"
OUTPUT_DIR="output/krimi_1min_kino_flow"
CHAR1_IMG="ComfyUI/input/detective_cross.png"
CHAR2_IMG="ComfyUI/input/elena_vance.png"

# Prüfe und erstelle Symlinks zu vorhandenen Assets falls nötig
if [ ! -f "$CHAR1_IMG" ]; then
    if [ -f "ComfyUI/input/YOTTEA-KREA-PRO (21).png" ]; then
        ln -sf "YOTTEA-KREA-PRO (21).png" "$CHAR1_IMG"
    fi
fi

if [ ! -f "$CHAR2_IMG" ]; then
    if [ -f "ComfyUI/input/T345KT05NWV2K1T38NJFWZCNY0.png" ]; then
        ln -sf "T345KT05NWV2K1T38NJFWZCNY0.png" "$CHAR2_IMG"
    fi
fi

# Standardwerte
SELECTED_MP="0.6"
SELECTED_STEPS="10"
ENABLE_UPSCALE=true
HARD_CUTS=true
FAN_PROFILE="sweet-spot"
FAN_MANAGED=false

# Interaktive Abfrage nur wenn Terminal aktiv ist und keine Flags übergeben wurden
if [ -t 0 ] && [ "$#" -eq 0 ]; then
    echo "=================================================================="
    echo " 🎬 1-Minuten Film-Produktion: Interaktiver Setup-Assistent"
    echo "=================================================================="
    echo ""

    # --- 1. W7800 Lüfter & Kühlprofil ---
    echo "🌀 [1/3] W7800 LÜFTER- & POWER-PROFIL WÄHLEN:"
    echo "   [1] 🌟 Sweet-Spot (Empfohlen): 205W, 55% Lüfter (~74°C, leise & kühl)"
    echo "   [2] 🚀 Performance-Boost:     230W, 65% Lüfter (max. Taktung, thermisch stabil)"
    echo "   [3] ❄️ Extreme-Cooling:       230W, 85% Lüfter (maximale Kühlung für Dauerlast)"
    echo "   [4] 🔇 Silent / Desktop:       150W, 40% Lüfter (flüsterleise)"
    echo "   [5] ⚙️ Standard Automatik:    vBIOS-Automatik (keine manuelle Regelung)"
    read -p "   Ihre Auswahl [1-5, Standard: 1]: " fan_choice
    case "$fan_choice" in
        2) FAN_PROFILE="boost" ;;
        3) FAN_PROFILE="set-fan 85" ;;
        4) FAN_PROFILE="set-fan 40" ;;
        5) FAN_PROFILE="auto" ;;
        *) FAN_PROFILE="sweet-spot" ;;
    esac
    echo "   👉 Gewählt: $FAN_PROFILE"
    echo ""

    # --- 2. Auflösung (Megapixel) ---
    echo "📐 [2/3] NATIVE DIFFUSIONS-AUFLÖSUNG (MEGAPIXEL) WÄHLEN:"
    echo "   [1] 🌟 0.6 MP (1056x608) — Golden Sweet Spot (+55% mehr native Pixel) [Empfohlen]"
    echo "   [2] ⚡ 0.4 MP (864x480)  — Schneller Baseline-Modus (~80s pro Szene)"
    echo "   [3] 🎬 0.7 MP (1152x640) — Hohe Schärfe (+78% mehr Pixel)"
    echo "   [4] 👑 0.98 MP (1344x768)— Offizielles MiniMax-Maximum (Kino-Master)"
    read -p "   Ihre Auswahl [1-4, Standard: 1]: " mp_choice
    case "$mp_choice" in
        2) SELECTED_MP="0.4"; SELECTED_STEPS="8" ;;
        3) SELECTED_MP="0.7"; SELECTED_STEPS="10" ;;
        4) SELECTED_MP="0.98"; SELECTED_STEPS="12" ;;
        *) SELECTED_MP="0.6"; SELECTED_STEPS="10" ;;
    esac
    echo "   👉 Gewählt: $SELECTED_MP MP ($SELECTED_STEPS Steps)"
    echo ""

    # --- 3. KI-Upscaling ---
    echo "🔍 [3/3] NEURONALES KI-UPSCALING AUF FULL HD (1080p):"
    echo "   [1] 🌟 Ja: Real-ESRGAN 4x+ Supersampling auf 1080p [Empfohlen]"
    echo "   [2] ⏩ Nein: Nur native Auflösung belassen (schnellster Durchlauf)"
    read -p "   Ihre Auswahl [1-2, Standard: 1]: " up_choice
    case "$up_choice" in
        2) ENABLE_UPSCALE=false ;;
        *) ENABLE_UPSCALE=true ;;
    esac
    echo "   👉 Gewählt: $([ "$ENABLE_UPSCALE" = true ] && echo "Ja (1080p KI-Upscaling)" || echo "Nein (Native Auflösung)")"
    echo "=================================================================="
    echo ""
fi

# CLI-Argumente parsen (falls vorhanden, überschreiben sie die Defaults)
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --fan)
            FAN_PROFILE="$2"
            shift 2
            ;;
        --no-fan)
            FAN_PROFILE="auto"
            shift
            ;;
        --no-upscale)
            ENABLE_UPSCALE=false
            shift
            ;;
        --upscale)
            ENABLE_UPSCALE=true
            shift
            ;;
        --mp)
            SELECTED_MP="$2"
            shift 2
            ;;
        --smooth)
            HARD_CUTS=false
            shift
            ;;
        --hard-cuts)
            HARD_CUTS=true
            shift
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

# Sicherheits-Trap: Bei Skriptende oder Abbruch (Ctrl+C) Lüfter zurück auf Automatik setzen
cleanup_fan_on_exit() {
    if [ "$FAN_MANAGED" = true ] && [ -f "scripts/w7800_perf_boost.sh" ]; then
        echo ""
        echo "🌀 Setze W7800 Lüftersteuerung sicher zurück auf vBIOS-Automatik..."
        sudo ./scripts/w7800_perf_boost.sh auto >/dev/null 2>&1 || true
    fi
}
trap cleanup_fan_on_exit EXIT INT TERM

# W7800 Lüfter- & Power-Profil anwenden
if [ -f "scripts/w7800_perf_boost.sh" ] && [ "$FAN_PROFILE" != "auto" ]; then
    echo "🌀 Wende Lüfterprofil '$FAN_PROFILE' auf AMD Radeon PRO W7800 an..."
    if command -v sudo >/dev/null 2>&1; then
        if sudo ./scripts/w7800_perf_boost.sh $FAN_PROFILE; then
            FAN_MANAGED=true
            echo "✅ Lüfterprofil aktiv."
        else
            echo "⚠️ Konnte Lüfterprofil nicht setzen (Passwort-Prompt abgelehnt?). Fahre mit vBIOS fort."
        fi
    fi
    echo ""
fi

echo "=================================================================="
echo " 🎬 Starte 1-Minuten 2-Personen Thriller-Pipeline (12 Szenen à 5s = 60s)"
echo "=================================================================="
echo " Storyboard:        $STORY_FILE"
echo " Charakter 1:       $CHAR1_IMG (<Picture 1> Detective Cross)"
echo " Charakter 2:       $CHAR2_IMG (<Picture 2> Elena Vance)"
echo " Ausgabepfad:       $OUTPUT_DIR"
echo " Auflösung:         $SELECTED_MP Megapixel"
echo " Sampling Steps:    $SELECTED_STEPS Steps"
echo " KI-Upscaling:      $([ "$ENABLE_UPSCALE" = true ] && echo "Aktiviert (Real-ESRGAN auf 1080p)" || echo "Deaktiviert")"
echo " W7800 Kühlung:     $FAN_PROFILE"
echo " Zusätzliche Flags: ${EXTRA_ARGS[*]}"
echo "=================================================================="

# Aktiviere die ComfyUI Python-Umgebung
if [ -d "comfy_env" ]; then
    source comfy_env/bin/activate
fi

# Performance-Tuning für AMD ROCm 6.4 & RDNA3 Matrix-Multiplikation
export TORCH_BLAS_PREFER_HIPBLASLT=1
export AMD_SERIALIZE_KERNEL=0
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Baue Aufruf-Argumente
CMD_ARGS=(
    scripts/auto_movie_maker.py
    --story "$STORY_FILE"
    --character "$CHAR1_IMG"
    --character2 "$CHAR2_IMG"
    --output "$OUTPUT_DIR"
    --mp "$SELECTED_MP"
    --steps "$SELECTED_STEPS"
    --duration 5.0
)

if [ "$ENABLE_UPSCALE" = true ]; then
    CMD_ARGS+=(--upscale)
fi

if [ "$HARD_CUTS" = true ]; then
    CMD_ARGS+=(--hard-cuts)
fi

if [ ${#EXTRA_ARGS[@]} -gt 0 ]; then
    CMD_ARGS+=("${EXTRA_ARGS[@]}")
fi

# Starte Pipeline
python3 "${CMD_ARGS[@]}"

echo ""
echo "=================================================================="
echo " ✅ Film-Pipeline erfolgreich durchgelaufen!"
echo " 📁 Ausgabeverzeichnis: $OUTPUT_DIR"
echo " 📄 Vollständiges Log:  $OUTPUT_DIR/production.log"
echo "=================================================================="

# Automatische Systembereinigung am Ende (RAM, Caches & SWAP)
if [ -f "scripts/free_vram.sh" ]; then
    echo ""
    echo "🧹 Führe abschließende Systembereinigung durch (RAM + SWAP leeren)..."
    ./scripts/free_vram.sh || true
fi
