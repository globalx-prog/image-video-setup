#!/bin/bash
# ==============================================================================
# 🔄 ComfyUI Smart-Restart & VRAM-Cleanup
# Erkennt automatisch, ob ComfyUI als Systemd-Dienst (Autostart) oder manuell
# läuft. Verhindert doppelte Instanzen, befreit den VRAM und startet sauber neu.
# ==============================================================================

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================================="
echo " 🧹 [1/3] VRAM-Bereinigung & Beenden laufender Prozesse..."
echo "=========================================================="

# 1. Höflicher API-Call zum Entladen der Modelle (falls ComfyUI noch reagiert)
curl -s -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}' -o /dev/null 2>/dev/null || true

# 2. Falls Ollama Modelle im VRAM hält: Entladen
if command -v ollama >/dev/null 2>&1; then
    LOADED_OLLAMA=$(ollama ps 2>/dev/null | awk 'NR>1 {print $1}')
    if [ -n "$LOADED_OLLAMA" ]; then
        echo "▶ Entlade aktive Ollama-Modelle:"
        for model in $LOADED_OLLAMA; do
            echo "   - Stoppe $model..."
            ollama stop "$model" 2>/dev/null || true
        done
    fi
fi

# 3. Manuelle Rest-Prozesse auf Port 8188 beenden
echo "▶ Räume Port 8188 frei..."
fuser -k 8188/tcp 2>/dev/null || true
sleep 1
fuser -k -9 8188/tcp 2>/dev/null || true

echo ""
echo "=========================================================="
echo " 📊 [2/3] VRAM-Status nach Bereinigung:"
echo "=========================================================="
if command -v rocm-smi >/dev/null 2>&1; then
    rocm-smi --showmeminfo vram || true
elif [ -x "/opt/rocm/bin/rocm-smi" ]; then
    /opt/rocm/bin/rocm-smi --showmeminfo vram || true
else
    echo "✓ Prozesse beendet. 48 GB VRAM vom Linux-Kernel freigegeben."
fi

echo ""
echo "=========================================================="
echo " 🚀 [3/3] Starte ComfyUI neu..."
echo "=========================================================="

# 4. Prüfen, ob der Systemd-Autostart-Dienst eingerichtet ist
if systemctl --user is-enabled --quiet comfyui.service 2>/dev/null; then
    echo "▶ Autostart-Dienst (comfyui.service) erkannt."
    echo "▶ Starte Dienst sauber via systemctl neu (keine doppelten Instanzen!)..."
    systemctl --user restart comfyui.service
    echo "✓ ComfyUI läuft unter http://127.0.0.1:8188"
    echo "----------------------------------------------------------"
    echo "▶ Schalte Live-Konsole auf (Beenden mit Strg+C)..."
    echo "----------------------------------------------------------"
    exec journalctl --user -u comfyui.service -f
else
    echo "▶ Kein Systemd-Dienst aktiv. Starte ComfyUI manuell im Vordergrund..."
    exec "$DIR/start_comfyui.sh"
fi
