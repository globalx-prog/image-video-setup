#!/bin/bash
# Startet ComfyUI (native AMD/ROCm). Port 8188 auf allen Interfaces,
# damit Open WebUI (Docker) über die Tailscale-IP zugreifen kann.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/../comfy_env" ]; then
    cd "$SCRIPT_DIR/.."
else
    cd "$SCRIPT_DIR"
fi
source comfy_env/bin/activate
cd ComfyUI

# ROCm & PyTorch Stabilitäts-Optimierungen für AMD Radeon PRO W7800
# 1. Verhindert Speicherfragmentierung bei großen Diffusionsmodellen
export PYTORCH_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"
export PYTORCH_CUDA_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"
# 2. Vermeidet SDMA-Hardware-Ring Deadlocks bei PCIe Transfers
export HSA_ENABLE_SDMA=0

# Startparameter:
# --reserve-vram 3        : Schützt 3 GB VRAM für den Desktop (GNOME/Wayland)
# --cache-ram 4 16        : Begrenzt Host-RAM-Caching (4 GB aktiv, 16 GB max), verhindert Swap-Thrashing
# --disable-pinned-memory : Verhindert das Sperren von 43 GB RAM via hipHostRegister (vermeidet 19 GB Swap-Stau bei FLUX.2!)
# --disable-async-offload : Nutzt sauberes mmap statt doppelter HostBuffer-Kopien im RAM
# --fp32-vae              : Zwingt VAE in FP32 (verhindert NaN-Überlauf / komplett schwarze Bilder bei SDXL auf AMD ROCm)
exec python main.py --reserve-vram 3 --cache-ram 4 16 --disable-pinned-memory --disable-async-offload --fp32-vae --listen 0.0.0.0 --port 8188
