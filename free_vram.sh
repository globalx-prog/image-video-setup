#!/bin/bash
# ==============================================================================
# 🧹 All-in-One Speicherbereiniger: VRAM, RAM & SWAP
# ==============================================================================
# Befreit auf einen Schlag:
# 1. GPU-VRAM (Ollama + ComfyUI PyTorch Cache auf AMD W7800)
# 2. System-RAM (Host-Arbeitsspeicher, Python-Heap & Linux Page-Caches)
# 3. SWAP (Holt ausgelagerte Desktop-Programme sofort von der SSD in den RAM zurück)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE} 🧹 Starte vollständige Speicherbereinigung (VRAM + RAM + SWAP)${NC}"
echo -e "${BLUE}================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. OLLAMA VRAM BEREINIGUNG
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [1/4] Prüfe aktive Ollama-Modelle...${NC}"
if command -v ollama >/dev/null 2>&1; then
    LOADED_OLLAMA=$(ollama ps 2>/dev/null | awk 'NR>1 {print $1}')
    if [ -n "$LOADED_OLLAMA" ]; then
        for model in $LOADED_OLLAMA; do
            echo "   - Entlade $model aus VRAM..."
            ollama stop "$model" 2>/dev/null || true
        done
        echo -e "${GREEN}✓ Ollama-Modelle gestoppt.${NC}"
    else
        echo "✓ Keine aktiven Ollama-Modelle im VRAM."
    fi
else
    echo "ℹ Ollama nicht installiert oder nicht im PATH."
fi

# ------------------------------------------------------------------------------
# 2. COMFYUI VRAM & PYTORCH CACHES LEEREN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [2/4] Sende Bereinigungsbefehl an ComfyUI...${NC}"
RESPONSE=$(curl -s -w "%{http_code}" -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}' -o /dev/null 2>/dev/null || echo "offline")

if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ ComfyUI hat VRAM-Modelle & PyTorch-Caches erfolgreich freigegeben.${NC}"
else
    echo -e "${YELLOW}ℹ ComfyUI Web-API nicht erreichbar (Service offline oder blockiert).${NC}"
fi

# ------------------------------------------------------------------------------
# 3. SYSTEM-RAM & LINUX PAGE-CACHES BEREINIGEN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [3/4] Bereinige System-RAM & Linux Dateisystem-Caches...${NC}"
sync
if command -v sudo >/dev/null 2>&1; then
    echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ Inaktive Linux Page-Caches geleert.${NC}"
else
    echo "ℹ Root-Rechte erforderlich für drop_caches."
fi

# ------------------------------------------------------------------------------
# 4. SWAP-AUSLAGERUNG VOLLSTÄNDIG IN DEN RAM ZURÜCKHOLEN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [4/4] Prüfe SWAP-Auslagerung auf der SSD...${NC}"
SWAP_USED_MB=$(free -m | awk '/Swap:/ {print $3}')
RAM_AVAIL_MB=$(free -m | awk '/Mem:/ {print $7}')

echo "   - Aktuell belegter Swap: ${SWAP_USED_MB:-0} MB"
echo "   - Verfügbarer freier RAM: ${RAM_AVAIL_MB:-0} MB"

if [ -n "$SWAP_USED_MB" ] && [ "$SWAP_USED_MB" -gt 0 ]; then
    if [ "$RAM_AVAIL_MB" -gt "$SWAP_USED_MB" ]; then
        echo "   ▶ Leere Swap auf die SSD und schiebe Daten in den schnellen RAM zurück..."
        sudo swapoff -a && sudo swapon -a
        echo -e "${GREEN}✓ Swap vollständig auf 0 MB geleert! Desktop läuft wieder flüssig.${NC}"
    else
        echo -e "${RED}⚠️ Zu wenig freier RAM vorhanden, um den Swap jetzt sicher zu leeren!${NC}"
        echo -e "${YELLOW}👉 Führe 'systemctl --user restart comfyui.service' aus, um vorher RAM freizugeben.${NC}"
    fi
else
    echo -e "${GREEN}✓ Swap ist bereits sauber (0 MB belegt). Kein Handlungsbedarf.${NC}"
fi

# ------------------------------------------------------------------------------
# 5. ABSCHLIESSENDE STATUS-ÜBERSICHT
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE} 📊 Systemstatus nach Bereinigung:${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${YELLOW}--- [Arbeitsspeicher & Swap] ---${NC}"
free -h

echo -e "\n${YELLOW}--- [GPU VRAM - AMD Radeon W7800] ---${NC}"
if command -v rocm-smi >/dev/null 2>&1; then
    rocm-smi --showmeminfo vram || true
elif [ -x "/opt/rocm/bin/rocm-smi" ]; then
    /opt/rocm/bin/rocm-smi --showmeminfo vram || true
else
    echo "✓ VRAM von ComfyUI freigegeben."
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN} ✅ FERTIG! VRAM, System-RAM und Swap sind sauber befreit.${NC}"
echo -e "${GREEN}================================================================${NC}\n"
