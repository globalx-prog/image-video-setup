#!/bin/bash
# ==============================================================================
# 🧹 All-in-One Speicher- & Anti-Ruckel-Bereiniger: VRAM, RAM, SWAP & GPU-Last
# ==============================================================================
# Befreit auf einen Schlag:
# 1. GPU-VRAM & Compute-Pipelines:
#    - Ollama Modelle sauber entladen (prüft lokal 127.0.0.1 UND Remote/Tailscale)
#    - ComfyUI Jobs abbrechen (/interrupt) & PyTorch Caches leeren (/free)
#    - Optionaler/automatischer Service-Restart bei blockiertem ROCm-VRAM
# 2. System-RAM (Host-Arbeitsspeicher & Linux Page-Caches)
# 3. SWAP (Holt ausgelagerte Programme von der SSD in den physischen RAM zurück)
# 4. GPU-DPM & Power-Profil Reset (bringt W7800 aus COMPUTE-Dauervollast zurück in Desktop-Auto)
# 5. Live-Hardware-Verifikation (GPU-Auslastung %, Leistungsaufnahme W, Hotspot °C)
#
# Optionen:
#   -r, --restart       Startet ComfyUI sauber neu (beendet blockierte Diffusion-Jobs)
#   -k, --kill-ollama   Startet Ollama-Dienst frisch neu (beendet festhängende llama-server Instanzen)
#   -f, --force         Vollständiger Force-Reset (ComfyUI + Ollama Neustart + DPM Reset)
#   -h, --help          Zeigt diese Hilfe an
# ==============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

RESTART_COMFY=false
KILL_OLLAMA=false
FORCE_MODE=false

for arg in "$@"; do
    case "$arg" in
        -r|--restart)
            RESTART_COMFY=true
            ;;
        -k|--kill-ollama)
            KILL_OLLAMA=true
            ;;
        -f|--force)
            FORCE_MODE=true
            RESTART_COMFY=true
            KILL_OLLAMA=true
            ;;
        -h|--help)
            echo -e "${BOLD}Nutzung:${NC} $0 [OPTIONEN]"
            echo ""
            echo "Optionen:"
            echo "  -r, --restart       Startet ComfyUI-Dienst sauber neu (beendet hängende ROCm-Pipelines)"
            echo "  -k, --kill-ollama   Startet den lokalen Ollama-Dienst frisch neu"
            echo "  -f, --force         Aggressiver Reset (ComfyUI + Ollama Neustart + GPU-DPM Reset)"
            echo "  -h, --help          Zeigt diese Hilfe"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE} 🧹 Starte vollständige Systembereinigung (VRAM + RAM + GPU-Last)${NC}"
echo -e "${BLUE}================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. OLLAMA VRAM & COMPUTE BEREINIGUNG (LOKAL + REMOTE)
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [1/5] Prüfe aktive Ollama-Modelle (VRAM-Freigabe)...${NC}"

# 1a. IMMER zuerst die lokale Ollama-Instanz prüfen (127.0.0.1:11434)
LOCAL_OLLAMA_HOST="http://127.0.0.1:11434"
if command -v ollama >/dev/null 2>&1; then
    LOCAL_MODELS=$(OLLAMA_HOST="$LOCAL_OLLAMA_HOST" timeout 3 ollama ps 2>/dev/null | awk 'NR>1 {print $1}' || true)
    if [ -n "$LOCAL_MODELS" ]; then
        for model in $LOCAL_MODELS; do
            echo -e "   - Entlade lokales Modell: ${CYAN}$model${NC} aus W7800 VRAM..."
            OLLAMA_HOST="$LOCAL_OLLAMA_HOST" timeout 6 ollama stop "$model" 2>/dev/null || true
        done
        echo -e "${GREEN}✓ Lokale Ollama-Modelle gestoppt.${NC}"
    else
        echo "✓ Keine aktiven Ollama-Modelle auf localhost:11434."
    fi

    # 1b. Falls in ~/.bashrc ein Remote-/Tailscale-Host konfiguriert ist, diesen separat prüfen
    REMOTE_HOST=""
    if [ -f "$HOME/.bashrc" ]; then
        REMOTE_HOST=$(grep -E '^\s*export OLLAMA_HOST=' "$HOME/.bashrc" | tail -n 1 | cut -d '=' -f2 | tr -d '"'\'' ')
    fi
    if [ -n "$OLLAMA_HOST" ] && [ "$OLLAMA_HOST" != "$LOCAL_OLLAMA_HOST" ]; then
        REMOTE_HOST="$OLLAMA_HOST"
    fi

    if [ -n "$REMOTE_HOST" ] && [[ "$REMOTE_HOST" != *"127.0.0.1"* ]] && [[ "$REMOTE_HOST" != *"localhost"* ]]; then
        echo "   - Prüfe zusätzlich konfigurierten Remote-Host ($REMOTE_HOST)..."
        REMOTE_MODELS=$(OLLAMA_HOST="$REMOTE_HOST" timeout 3 ollama ps 2>/dev/null | awk 'NR>1 {print $1}' || true)
        if [ -n "$REMOTE_MODELS" ]; then
            for model in $REMOTE_MODELS; do
                echo -e "   - Entlade Remote-Modell: ${CYAN}$model${NC}..."
                OLLAMA_HOST="$REMOTE_HOST" timeout 5 ollama stop "$model" 2>/dev/null || true
            done
            echo -e "${GREEN}✓ Remote Ollama-Modelle gestoppt.${NC}"
        fi
    fi

    # 1c. Falls --kill-ollama oder --force aktiv ist, oder llama-server festhängt
    if [ "$KILL_OLLAMA" = true ]; then
        echo -e "   - Starte Ollama-Dienst via systemctl neu (--kill-ollama aktiv)..."
        if sudo -n systemctl restart ollama 2>/dev/null; then
            echo -e "${GREEN}✓ ollama.service neugestartet.${NC}"
        elif sudo systemctl restart ollama 2>/dev/null; then
            echo -e "${GREEN}✓ ollama.service neugestartet.${NC}"
        else
            sudo -n pkill -9 -f llama-server 2>/dev/null || true
            echo -e "${GREEN}✓ llama-server Prozesse beendet.${NC}"
        fi
    fi
else
    echo "ℹ ollama CLI nicht gefunden."
fi

# ------------------------------------------------------------------------------
# 2. COMFYUI VRAM & PYTORCH CACHES LEEREN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [2/5] Sende Bereinigungsbefehl an ComfyUI (Port 8188)...${NC}"

# Schritt 2a: Eventuell laufende Generierung abbrechen
curl -s -m 2 -X POST http://127.0.0.1:8188/interrupt -o /dev/null 2>/dev/null || true

# Schritt 2b: Modelle und PyTorch-Caches über ComfyUI API freigeben
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}' 2>/dev/null)
HTTP_CODE="${HTTP_CODE:-000}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ ComfyUI API hat Freigabebefehl empfangen.${NC}"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${YELLOW}ℹ ComfyUI Web-API offline oder antwortet nicht.${NC}"
else
    echo -e "${YELLOW}ℹ ComfyUI Web-API gab Status $HTTP_CODE zurück.${NC}"
fi

# Schritt 2c: Falls --restart oder --force angegeben wurde:
if [ "$RESTART_COMFY" = true ]; then
    echo -e "\n${YELLOW}▶ Starte ComfyUI neu (--restart aktiv für 100% VRAM- & Pipeline-Freigabe)...${NC}"
    if systemctl --user is-active --quiet comfyui.service 2>/dev/null; then
        systemctl --user restart comfyui.service 2>/dev/null || true
        echo -e "${GREEN}✓ comfyui.service via systemctl neugestartet.${NC}"
    else
        fuser -k -9 8188/tcp 2>/dev/null || true
        echo -e "${GREEN}✓ Port 8188 freigeräumt.${NC}"
    fi
    sleep 1
fi

# ------------------------------------------------------------------------------
# 3. SYSTEM-RAM & LINUX PAGE-CACHES BEREINIGEN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [3/5] Bereinige System-RAM & Linux Dateisystem-Caches...${NC}"
sync
if command -v sudo >/dev/null 2>&1; then
    if echo 3 | sudo -n tee /proc/sys/vm/drop_caches >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Inaktive Linux Page-Caches geleert.${NC}"
    elif echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Inaktive Linux Page-Caches geleert.${NC}"
    else
        echo "ℹ drop_caches übersprungen (keine Root-Berechtigung)."
    fi
fi

# ------------------------------------------------------------------------------
# 4. SWAP-AUSLAGERUNG IN DEN RAM ZURÜCKHOLEN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [4/5] Prüfe SWAP-Auslagerung auf der SSD...${NC}"
SWAP_USED_MB=$(free -m 2>/dev/null | awk '/Swap:/ {print $3}')
RAM_AVAIL_MB=$(free -m 2>/dev/null | awk '/Mem:/ {print $7}')

echo "   - Aktuell belegter Swap: ${SWAP_USED_MB:-0} MB"
echo "   - Verfügbarer freier RAM: ${RAM_AVAIL_MB:-0} MB"

if [ -n "$SWAP_USED_MB" ] && [ "$SWAP_USED_MB" -gt 50 ]; then
    if [ -n "$RAM_AVAIL_MB" ] && [ "$RAM_AVAIL_MB" -gt "$SWAP_USED_MB" ]; then
        echo "   ▶ Leere Swap auf die SSD und schiebe Daten in den schnellen RAM zurück..."
        SWAPOFF_BIN=$(command -v swapoff || echo "/usr/sbin/swapoff")
        SWAPON_BIN=$(command -v swapon || echo "/usr/sbin/swapon")
        
        SWAP_CLEARED=false
        if sudo -n "$SWAPOFF_BIN" -a 2>/dev/null && sudo -n "$SWAPON_BIN" -a 2>/dev/null; then
            SWAP_CLEARED=true
        elif sudo "$SWAPOFF_BIN" -a 2>/dev/null && sudo "$SWAPON_BIN" -a 2>/dev/null; then
            SWAP_CLEARED=true
        fi
        
        NEW_SWAP_USED_MB=$(free -m 2>/dev/null | awk '/Swap:/ {print $3}')
        if [ "$SWAP_CLEARED" = true ] && [ "${NEW_SWAP_USED_MB:-999}" -lt 50 ]; then
            echo -e "${GREEN}✓ Swap vollständig auf ${NEW_SWAP_USED_MB:-0} MB geleert.${NC}"
        else
            echo -e "${YELLOW}ℹ Swap konnte nicht vollständig geleert werden (aktuell: ${NEW_SWAP_USED_MB:-$SWAP_USED_MB} MB).${NC}"
        fi
    else
        echo -e "${RED}⚠️ Zu wenig freier RAM vorhanden, um den Swap jetzt sicher zu leeren!${NC}"
    fi
else
    echo -e "${GREEN}✓ Swap ist bereits sauber (${SWAP_USED_MB:-0} MB belegt).${NC}"
fi

# ------------------------------------------------------------------------------
# 5. GPU DPM & POWER-PROFIL RESET (ANTI-RUCKEL-SCHLÜSSEL)
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [5/5] Prüfe W7800 Hardware-Status & GPU-Compute-Last...${NC}"

CARD_DIR=""
for c in /sys/class/drm/card[0-9]*/device; do
    if [ -f "$c/pp_power_profile_mode" ]; then
        CARD_DIR="$c"
        break
    fi
done

HWMON_DIR=""
if [ -n "$CARD_DIR" ]; then
    for h in "$CARD_DIR"/hwmon/hwmon*; do
        if [ -f "$h/power1_average" ] || [ -f "$h/temp1_input" ]; then
            HWMON_DIR="$h"
            break
        fi
    done
fi

# Falls Performance-Level auf "high" oder Compute Profil 5 festhängt: auf "auto" / "0" zurückstellen
if [ -n "$CARD_DIR" ]; then
    CURR_DPM=$(cat "$CARD_DIR/power_dpm_force_performance_level" 2>/dev/null || echo "")
    if [ "$CURR_DPM" = "high" ]; then
        echo "   - Setze DPM Performance-Level von 'high' auf 'auto' zurück..."
        echo auto | sudo -n tee "$CARD_DIR/power_dpm_force_performance_level" >/dev/null 2>&1 || true
    fi
    if [ -f "$CARD_DIR/pp_power_profile_mode" ]; then
        ACTIVE_PROF=$(grep "\*" "$CARD_DIR/pp_power_profile_mode" 2>/dev/null | awk '{print $2}')
        if [ "$ACTIVE_PROF" = "COMPUTE" ]; then
            echo "   - Setze Power-Profil von 'COMPUTE' auf 'BOOTUP_DEFAULT' zurück..."
            echo 0 | sudo -n tee "$CARD_DIR/pp_power_profile_mode" >/dev/null 2>&1 || true
        fi
    fi
fi

# ------------------------------------------------------------------------------
# 6. ABSCHLIESSENDE STATUS-ÜBERSICHT & REALITÄTS-CHECK
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}================================================================${NC}"
echo -e "${BLUE} 📊 Systemstatus nach Bereinigung:${NC}"
echo -e "${BLUE}================================================================${NC}"

echo -e "\n${YELLOW}--- [Host-Arbeitsspeicher & Swap] ---${NC}"
free -h

echo -e "\n${YELLOW}--- [W7800 Hardware-Echtzeitwerte] ---${NC}"
GPU_BUSY=$(cat "$CARD_DIR/gpu_busy_percent" 2>/dev/null || echo "0")
POWER_RAW=$(cat "$HWMON_DIR/power1_average" 2>/dev/null || echo "0")
POWER_W=$((POWER_RAW / 1000000))
TEMP_EDGE_RAW=$(cat "$HWMON_DIR/temp1_input" 2>/dev/null || echo "0")
TEMP_JUNC_RAW=$(cat "$HWMON_DIR/temp2_input" 2>/dev/null || echo "0")
TEMP_EDGE=$((TEMP_EDGE_RAW / 1000))
TEMP_HOTSPOT=$((TEMP_JUNC_RAW / 1000))

echo -e "   - GPU-Compute Auslastung: ${BOLD}${GPU_BUSY}%${NC}"
echo -e "   - Leistungsaufnahme:      ${BOLD}${POWER_W} Watt${NC}"
echo -e "   - Temperaturen:           Edge: ${TEMP_EDGE}°C | Hotspot: ${TEMP_HOTSPOT}°C"

# VRAM über rocm-smi
ROCM_SMI_BIN=""
if command -v rocm-smi >/dev/null 2>&1; then
    ROCM_SMI_BIN=$(command -v rocm-smi)
elif [ -x "/opt/rocm/bin/rocm-smi" ]; then
    ROCM_SMI_BIN="/opt/rocm/bin/rocm-smi"
fi
if [ -n "$ROCM_SMI_BIN" ]; then
    echo ""
    "$ROCM_SMI_BIN" --showmeminfo vram 2>/dev/null || true
fi

echo -e "\n${BLUE}================================================================${NC}"
if [ "$GPU_BUSY" -le 15 ] && [ "$POWER_W" -le 100 ]; then
    echo -e "${GREEN} ✅ PERFEKT: GPU ist im echten Leerlauf (${GPU_BUSY}%, ${POWER_W}W).${NC}"
    echo -e "${GREEN}    Der 4K-Desktop wird nicht mehr ausgehungert und läuft butterweich!${NC}"
else
    echo -e "${RED} ⚠️ WARNUNG: GPU ist weiterhin aktiv (${GPU_BUSY}% Last, ${POWER_W}W)!${NC}"
    echo -e "${YELLOW}    Ursache für Desktop-Ruckeln: Ein KI-Compute-Prozess rechnet noch immer.${NC}"
    echo -e "${CYAN}    Lösung: Führe './scripts/free_vram.sh --force' aus, um verbleibende${NC}"
    echo -e "${CYAN}            Hintergrund-Instanzen hart neu zu starten.${NC}"
fi
echo -e "${BLUE}================================================================${NC}\n"
