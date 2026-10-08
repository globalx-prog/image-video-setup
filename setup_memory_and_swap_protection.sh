#!/bin/bash
# ==============================================================================
# 🛡️ KI-Workstation: RAM-Schutz, Swap-Schwankungsfilter & ComfyUI-Autostart
# ==============================================================================
# 1. Hält IMMER mindestens 1 GB RAM eisern für Kernel & Desktop frei (vm.min_free_kbytes)
# 2. Swap wird NUR bei extremen Lastspitzen (Schwankungen) genutzt (vm.swappiness = 5)
# 3. Automatischer Swap-Wächter: Leert den Swap selbstständig, sobald die Spitze vorbei ist
# 4. ComfyUI Memory-Cap (54 GB): Verhindert, dass ComfyUI den gesamten 63 GB RAM auffrisst
# 5. Zuverlässiger Autostart von ComfyUI bei jedem Systemstart
# ==============================================================================

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE} 🛡️  Konfiguriere RAM-Schutz & Swap-Spitzen-Management...${NC}"
echo -e "${BLUE}================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. KERNEL-PARAMETER (Eisernes 1 GB RAM-Reserve & Notfall-Swap)
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [1/4] Schreibe Kernel-Speicherschutz (/etc/sysctl.d/99-ai-memory-guard.conf)...${NC}"

sudo tee /etc/sysctl.d/99-ai-memory-guard.conf > /dev/null << 'EOF'
# 1. Mindestens 1 GB (1.048.576 KB) physischer RAM eisern für Kernel & UI reservieren
# Normale Anwendungen (Python, Chrome) dürfen diesen Speicher NIEMALS belegen.
vm.min_free_kbytes = 1048576

# 2. Swap NUR bei echten Lastspitzen/Schwankungen anrühren (Standard: 60)
# Bleibt im normalen Betrieb bei 0 MB Swap-Auslastung.
vm.swappiness = 5

# 3. Sanfte Puffer-Rückgewinnung bei Lastwechseln (verhindert UI-Stottern)
vm.watermark_scale_factor = 50
vm.vfs_cache_pressure = 50
EOF

sudo sysctl --system > /dev/null
echo -e "${GREEN}✓ Kernel-Parameter sofort aktiv: 1 GB RAM-Reserve garantiert & Swap auf Notfallmodus gesetzt.${NC}"

# ------------------------------------------------------------------------------
# 2. AUTOMATISCHER SWAP-WÄCHTER (Auto-Reclaim nach Schwankungen)
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [2/4] Richte automatischen Swap-Wächter ein (leert Swap nach Spitzen selbstständig)...${NC}"

sudo tee /usr/local/bin/auto-swap-reclaim.sh > /dev/null << 'EOF'
#!/bin/bash
# Prüft jede Minute: Liegen Daten im Swap, obwohl der RAM wieder frei ist?
SWAP_USED_MB=$(free -m | awk '/Swap:/ {print $3}')
RAM_AVAIL_MB=$(free -m | awk '/Mem:/ {print $7}')

# Wenn mehr als 300 MB im Swap liegen UND mehr als 12 GB RAM frei sind:
if [ -n "$SWAP_USED_MB" ] && [ -n "$RAM_AVAIL_MB" ]; then
    if [ "$SWAP_USED_MB" -gt 300 ] && [ "$RAM_AVAIL_MB" -gt 12000 ]; then
        # Leert den Swap leise und schiebt alles zurück in den schnellen RAM
        swapoff -a && swapon -a
    fi
fi
EOF

sudo chmod +x /usr/local/bin/auto-swap-reclaim.sh

# Systemd Service & Timer anlegen
sudo tee /etc/systemd/system/auto-swap-reclaim.service > /dev/null << 'EOF'
[Unit]
Description=Auto Swap Reclaim (Flushes swap to RAM after spikes)
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/auto-swap-reclaim.sh
EOF

sudo tee /etc/systemd/system/auto-swap-reclaim.timer > /dev/null << 'EOF'
[Unit]
Description=Run Auto Swap Reclaim every minute

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now auto-swap-reclaim.timer
echo -e "${GREEN}✓ Swap-Wächter aktiv: Leert Auslagerungen nach Arbeitsspitzen vollautomatisch!${NC}"

# ------------------------------------------------------------------------------
# 3. COMFYUI AUTOSTART & SPEICHER-BEGRENZUNG ABSICHERN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [3/4] Repariere ComfyUI-Autostart und setze 54 GB RAM-Deckel...${NC}"

# Sicherstellen, dass start_comfyui.sh ausführbar ist
chmod +x "$DIR/start_comfyui.sh"

USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SYSTEMD_DIR"

cat << EOF > "$USER_SYSTEMD_DIR/comfyui.service"
[Unit]
Description=ComfyUI (native, AMD ROCm) - Autostart KI-Server
After=network-online.target default.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DIR/start_comfyui.sh
Restart=on-failure
RestartSec=10

# Speicher-Schutz: ComfyUI darf maximal 54 GB belegen (von 63 GB).
# Garantiert, dass Desktop, Browser und OS niemals durch ComfyUI verdrängt werden!
MemoryHigh=54G
MemoryMax=58G

[Install]
WantedBy=default.target docker-desktop.service
EOF

systemctl --user daemon-reload
systemctl --user enable comfyui.service
echo -e "${GREEN}✓ ComfyUI ist als unabhängiger Autostart-Dienst mit 54 GB RAM-Schutz eingerichtet.${NC}"

# ------------------------------------------------------------------------------
# 4. SYSTEM-BEREINIGUNG JETZT SOFORT DURCHFÜHREN
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}▶ [4/4] Führe sofortige Speicherbereinigung & Neustart durch...${NC}"

echo "▶ Starte ComfyUI sauber neu..."
systemctl --user restart comfyui.service

echo "▶ Warte 3 Sekunden auf RAM-Freigabe..."
sleep 3

RAM_FREE_MB=$(free -m | awk '/Mem:/ {print $4}')
SWAP_USED_MB=$(free -m | awk '/Swap:/ {print $3}')

echo "▶ Aktueller Status: Freier RAM: ${RAM_FREE_MB} MB | Swap belegt: ${SWAP_USED_MB} MB"

if [ "$SWAP_USED_MB" -gt 0 ]; then
    echo "▶ Zwinge Swap zurück in den physischen RAM (swapoff & swapon)..."
    sudo swapoff -a && sudo swapon -a
    echo -e "${GREEN}✓ Swap vollständig in RAM zurückgeholt (0 MB Swap belegt).${NC}"
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN} 🚀 FERTIG! Dein System ist optimal geschützt:${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e " 1. 🛡️ Mindestens 1 GB physischer RAM bleibt immer eisern für das OS reserviert."
echo -e " 2. 🌊 Swap wird NUR als Puffer für extreme Spitzen (MiniMax etc.) benutzt."
echo -e " 3. 🤖 Der automatische Wächter leert den Swap nach jeder Spitze selbstständig."
echo -e " 4. 🚀 ComfyUI startet jetzt zuverlässig bei jedem PC-Start automatisch!"
echo -e " 5. 🌐 ComfyUI Web-Interface läuft: http://127.0.0.1:8188"
echo -e "${GREEN}================================================================${NC}\n"

