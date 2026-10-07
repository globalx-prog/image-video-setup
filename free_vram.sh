#!/bin/bash
# ==============================================================================
# VRAM-Cleaner: Sofortige Speicherfreigabe für Ollama & ComfyUI
# Befreit die 48 GB AMD Radeon PRO W7800 von allen zwischengespeicherten Modellen.
# ==============================================================================

echo "=========================================================="
echo " 🧹 Starte VRAM-Bereinigung (Ollama + ComfyUI)"
echo "=========================================================="

# 1. Alle aktiven Ollama-Modelle aus dem VRAM entladen
LOADED_OLLAMA=$(ollama ps 2>/dev/null | awk 'NR>1 {print $1}')
if [ -n "$LOADED_OLLAMA" ]; then
    echo "▶ Entlade aktive Ollama-Modelle:"
    for model in $LOADED_OLLAMA; do
        echo "   - Stoppe $model..."
        ollama stop "$model" 2>/dev/null || true
    done
else
    echo "✓ Keine aktiven Ollama-Modelle im VRAM gefunden."
fi

# 2. ComfyUI auffordern, alle gecachten Modelle und PyTorch-VRAM-Caches zu leeren
echo "▶ Leere ComfyUI VRAM-Caches..."
RESPONSE=$(curl -s -w "%{http_code}" -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}' -o /dev/null || echo "offline")

if [ "$RESPONSE" = "200" ]; then
    echo "✓ ComfyUI Modelle & PyTorch VRAM erfolgreich freigegeben."
else
    echo "ℹ ComfyUI antwortet nicht (Service eventuell inaktiv)."
fi

# 3. Aktuelle VRAM-Auslastung anzeigen
echo ""
echo "=========================================================="
echo " 📊 Aktueller VRAM-Status nach Bereinigung:"
echo "=========================================================="
if command -v rocm-smi >/dev/null 2>&1; then
    rocm-smi --showmeminfo vram
else
    echo "rocm-smi nicht gefunden."
fi
echo "Fertig! Die GPU ist sauber für die nächste Generierung."

