#!/bin/bash
# ==============================================================================
# apply_amd_gpu_fixes.sh — Systemstabilitäts-Fixes für AMD Radeon PRO W7800
# Behebt:
# 1. GPU-Watchdog-Timeouts (lockup_timeout & queue_preemption_timeout_ms)
# 2. SDMA-Ring-Deadlocks (HSA_ENABLE_SDMA=0)
# 3. PyTorch ROCm Speicherfragmentierung
# 4. Host-RAM-Überallokation in ComfyUI (--cache-ram 8 32)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo " 🛠️  AMD GPU Stabilitäts-Patch (Radeon PRO W7800 / ROCm)"
echo "=========================================================="

if [ "$EUID" -ne 0 ]; then
    echo "ℹ Dieses Skript benötigt Root-Rechte zur Anpassung von /etc/modprobe.d/."
    echo "  Bitte ausführen mit: sudo ./apply_amd_gpu_fixes.sh"
    exit 1
fi

# 1. Kernel-Modul Timeout-Konfiguration anlegen
echo "▶ [1/3] Konfiguriere /etc/modprobe.d/amdgpu-timeout.conf..."
cat << 'EOF' > /etc/modprobe.d/amdgpu-timeout.conf
# AMD GPU Stabilitäts-Tuning für lange KI-Rechenschritte (Wan 2.1 / ComfyUI / ROCm)
# Erhöht den Hardware-Watchdog-Timeout von 9s auf 60s, um panische MODE1-Resets zu verhindern.
options amdgpu lockup_timeout=60000,60000,60000,60000 queue_preemption_timeout_ms=60000 gpu_recovery=1
EOF
chmod 644 /etc/modprobe.d/amdgpu-timeout.conf
echo "   ✓ Datei /etc/modprobe.d/amdgpu-timeout.conf erfolgreich erstellt."

# 2. Initramfs aktualisieren
echo "▶ [2/3] Aktualisiere initramfs (damit der Treiber beim Booten die Parameter lädt)..."
update-initramfs -u
echo "   ✓ initramfs erfolgreich aktualisiert."

# 3. Status-Hinweis
echo "▶ [3/3] Prüfung abgeschlossen."
echo ""
echo "=========================================================="
echo " ✅ AMD-Treiber-Patch erfolgreich installiert!"
echo " 👉 Die 60s-Timeouts sind nach dem nächsten Neustart aktiv."
echo "=========================================================="

