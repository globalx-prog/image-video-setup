#!/bin/bash
# ==============================================================================
# 🧹 All-in-One Speicherbereiniger: VRAM, RAM & SWAP
# ==============================================================================
# Befreit auf einen Schlag:
# 1. GPU-VRAM:
#    - Ollama Modelle sauber entladen (unterstützt lokale & Remote/Tailscale-Instanz)
#    - ComfyUI Jobs stoppen (/interrupt) & Modelle/Caches entladen (/free)
#    - Optionaler/automatischer Service-Restart bei hartnäckig belegtem ROCm-VRAM
# 2. System-RAM (Host-Arbeitsspeicher & Linux Page-Caches)
# 3. SWAP (Holt ausgelagerte Programme von der SSD in den physischen RAM zurück)
#
# Optionen:
#   --restart, -r   Startet ComfyUI nach der Bereinigung neu (garantiert 100% VRAM frei)
#   --help, -h      Zeigt diese Hilfe an
# ==============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

RESTART_COMFY=false
for arg in "$@"; do
    case "$arg" in
        -r|--restart)
            RESTART_COMFY=true
            ;;
        -h|--help)
            echo "Nutzung: $0 [OPTIONEN]"
            echo ""
            echo "Optionen:"
            echo "  -r, --restart   Startet den ComfyUI-Dienst sauber neu (garantiert 0 MB VRAM-Belegung)"
            echo "  -h, --help      Zeigt diese Hilfe"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE} 🧹 Starte vollständige Speicherbereinigung (VRAM + RAM + SWAP)${NC}"
echo -e "${BLUE}================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. OLLAMA VRAM BEREINIGUNG
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [1/4] Prüfe aktive Ollama-Modelle...${NC}"

# Falls OLLAMA_HOST nicht im Environment ist, prüfen wir gängige Konfigurationen (z.B. aus ~/.bashrc)
if [ -z "$OLLAMA_HOST" ] && [ -f "$HOME/.bashrc" ]; then
    DETECTED_HOST=$(grep -E '^\s*export OLLAMA_HOST=' "$HOME/.bashrc" | tail -n 1 | cut -d '=' -f2 | tr -d '"'\'' ')
    if [ -n "$DETECTED_HOST" ]; then
        export OLLAMA_HOST="$DETECTED_HOST"
    fi
fi

if command -v ollama >/dev/null 2>&1; then
    LOADED_OLLAMA=$(timeout 3 ollama ps 2>/dev/null | awk 'NR>1 {print $1}' || true)
    
    # Fallback auf localhost, falls remote/tailscale nicht erreichbar war
    if [ -z "$LOADED_OLLAMA" ] && [ -n "$OLLAMA_HOST" ]; then
        LOADED_OLLAMA=$(OLLAMA_HOST="127.0.0.1:11434" timeout 2 ollama ps 2>/dev/null | awk 'NR>1 {print $1}' || true)
    fi

    if [ -n "$LOADED_OLLAMA" ]; then
        for model in $LOADED_OLLAMA; do
            echo "   - Entlade $model aus VRAM..."
            timeout 5 ollama stop "$model" 2>/dev/null || true
        done
        echo -e "${GREEN}✓ Ollama-Modelle gestoppt.${NC}"
    else
        echo "✓ Keine aktiven Ollama-Modelle im VRAM gefunden."
    fi
else
    echo "ℹ Ollama nicht im PATH gefunden (wird übersprungen)."
fi

# ------------------------------------------------------------------------------
# 2. COMFYUI VRAM & PYTORCH CACHES LEEREN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [2/4] Sende Bereinigungsbefehl an ComfyUI (Port 8188)...${NC}"

# Schritt 2a: Eventuell laufende Generierung abbrechen, damit /free sofort greifen kann
curl -s -m 2 -X POST http://127.0.0.1:8188/interrupt -o /dev/null 2>/dev/null || true

# Schritt 2b: Modelle und PyTorch-Caches über ComfyUI API freigeben
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}' 2>/dev/null)
HTTP_CODE="${HTTP_CODE:-000}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ ComfyUI API hat Freigabebefehl empfangen.${NC}"
    echo "   - Warte 2 Sekunden auf Hintergrund-Entladevorgang und Garbage Collection..."
    sleep 2
    
    # Versuche ComfyUI System-Stats abzufragen
    STATS_JSON=$(curl -s -m 3 http://127.0.0.1:8188/system_stats 2>/dev/null || true)
    if [ -n "$STATS_JSON" ] && command -v python3 >/dev/null 2>&1; then
        VRAM_FREE_GB=$(python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(f\"{data.get('devices', [{}])[0].get('vram_free', 0) / (1024**3):.1f}\")" <<< "$STATS_JSON" 2>/dev/null || true)
        if [ -n "$VRAM_FREE_GB" ] && [ "$VRAM_FREE_GB" != "0.0" ]; then
            echo -e "   - Laut ComfyUI frei: ${CYAN}${VRAM_FREE_GB} GB VRAM${NC}"
        fi
    fi
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${YELLOW}ℹ ComfyUI Web-API nicht erreichbar (Service offline oder blockiert).${NC}"
else
    echo -e "${YELLOW}ℹ ComfyUI Web-API gab Status $HTTP_CODE zurück.${NC}"
fi

# Schritt 2c: Falls --restart angegeben wurde oder ComfyUI offline ist, sauber neustarten
if [ "$RESTART_COMFY" = true ]; then
    echo -e "\n${YELLOW}▶ Starte ComfyUI neu (--restart aktiv für 100% VRAM-Freigabe)...${NC}"
    if systemctl --user is-active --quiet comfyui.service 2>/dev/null; then
        systemctl --user restart comfyui.service 2>/dev/null || true
        echo -e "${GREEN}✓ comfyui.service via systemctl neugestartet.${NC}"
    else
        fuser -k -9 8188/tcp 2>/dev/null || true
        echo -e "${GREEN}✓ Port 8188 freigeräumt.${NC}"
    fi
    sleep 2
fi

# ------------------------------------------------------------------------------
# 3. SYSTEM-RAM & LINUX PAGE-CACHES BEREINIGEN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [3/4] Bereinige System-RAM & Linux Dateisystem-Caches...${NC}"
sync
if command -v sudo >/dev/null 2>&1; then
    if echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Inaktive Linux Page-Caches geleert.${NC}"
    else
        # Falls sudo ohne Passwort nicht erlaubt ist, versuchen wir es mit normalem sudo
        if echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Inaktive Linux Page-Caches geleert.${NC}"
        else
            echo "ℹ drop_caches übersprungen (keine Root-Berechtigung)."
        fi
    fi
else
    echo "ℹ sudo nicht verfügbar, drop_caches übersprungen."
fi

# ------------------------------------------------------------------------------
# 4. SWAP-AUSLAGERUNG VOLLSTÄNDIG IN DEN RAM ZURÜCKHOLEN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [4/4] Prüfe SWAP-Auslagerung auf der SSD...${NC}"
SWAP_USED_MB=$(free -m 2>/dev/null | awk '/Swap:/ {print $3}')
RAM_AVAIL_MB=$(free -m 2>/dev/null | awk '/Mem:/ {print $7}')

echo "   - Aktuell belegter Swap: ${SWAP_USED_MB:-0} MB"
echo "   - Verfügbarer freier RAM: ${RAM_AVAIL_MB:-0} MB"

if [ -n "$SWAP_USED_MB" ] && [ "$SWAP_USED_MB" -gt 50 ]; then
    if [ -n "$RAM_AVAIL_MB" ] && [ "$RAM_AVAIL_MB" -gt "$SWAP_USED_MB" ]; then
        echo "   ▶ Leere Swap auf die SSD und schiebe Daten in den schnellen RAM zurück..."
        
        # Pfad für swapoff/swapon (passend zur sudoers NOPASSWD-Regel)
        SWAPOFF_BIN=$(command -v swapoff || echo "/usr/sbin/swapoff")
        SWAPON_BIN=$(command -v swapon || echo "/usr/sbin/swapon")
        
        SWAP_CLEARED=false
        if sudo "$SWAPOFF_BIN" -a 2>/dev/null && sudo "$SWAPON_BIN" -a 2>/dev/null; then
            SWAP_CLEARED=true
        elif sudo swapoff -a 2>/dev/null && sudo swapon -a 2>/dev/null; then
            SWAP_CLEARED=true
        fi
        
        # Tatsächlichen Swap-Stand nach dem Befehl prüfen
        NEW_SWAP_USED_MB=$(free -m 2>/dev/null | awk '/Swap:/ {print $3}')
        if [ "$SWAP_CLEARED" = true ] && [ "${NEW_SWAP_USED_MB:-999}" -lt 50 ]; then
            echo -e "${GREEN}✓ Swap vollständig auf ${NEW_SWAP_USED_MB:-0} MB geleert! Desktop läuft wieder flüssig.${NC}"
        else
            echo -e "${YELLOW}ℹ Swap konnte nicht vollständig geleert werden (aktuell: ${NEW_SWAP_USED_MB:-$SWAP_USED_MB} MB). Root-Rechte prüfen.${NC}"
        fi
    else
        echo -e "${RED}⚠️ Zu wenig freier RAM vorhanden, um den Swap jetzt sicher zu leeren!${NC}"
        echo -e "${YELLOW}👉 Führe './free_vram.sh --restart' oder 'systemctl --user restart comfyui.service' aus.${NC}"
    fi
else
    echo -e "${GREEN}✓ Swap ist bereits sauber (${SWAP_USED_MB:-0} MB belegt). Kein Handlungsbedarf.${NC}"
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
ROCM_SMI_BIN=""
if command -v rocm-smi >/dev/null 2>&1; then
    ROCM_SMI_BIN=$(command -v rocm-smi)
elif [ -x "/usr/bin/rocm-smi" ]; then
    ROCM_SMI_BIN="/usr/bin/rocm-smi"
elif [ -x "/opt/rocm/bin/rocm-smi" ]; then
    ROCM_SMI_BIN="/opt/rocm/bin/rocm-smi"
else
    # Prüfe versionierte ROCm-Pfade wie /opt/rocm-7.2.3/bin/rocm-smi
    ROCM_CANDIDATE=$(find /opt -maxdepth 3 -name "rocm-smi" -type f -perm -111 2>/dev/null | head -n 1)
    if [ -n "$ROCM_CANDIDATE" ]; then
        ROCM_SMI_BIN="$ROCM_CANDIDATE"
    fi
fi

if [ -n "$ROCM_SMI_BIN" ]; then
    "$ROCM_SMI_BIN" --showmeminfo vram 2>/dev/null || true
else
    echo "ℹ rocm-smi nicht gefunden. VRAM-Status kann nicht direkt abgefragt werden."
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN} ✅ FERTIG! Speicherbereinigung abgeschlossen.${NC}"
if [ "$RESTART_COMFY" = false ]; then
    echo -e "${CYAN} 💡 Tipp: Falls der VRAM auf Treiberebene blockiert bleibt:${NC}"
    echo -e "${CYAN}    Führe './free_vram.sh --restart' aus (startet ComfyUI frisch neu).${NC}"
fi
echo -e "${GREEN}================================================================${NC}\n"
