#!/bin/bash
# Startet ComfyUI (native AMD/ROCm). Port 8188 auf allen Interfaces,
# damit Open WebUI (Docker) über die Tailscale-IP zugreifen kann.
cd "$(dirname "$0")"
source comfy_env/bin/activate
cd ComfyUI

# ROCm & PyTorch Stabilitäts-Optimierungen für AMD Radeon PRO W7800
# 1. Verhindert Speicherfragmentierung bei großen Diffusionsmodellen
export PYTORCH_CUDA_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"
# 2. Vermeidet SDMA-Hardware-Ring Deadlocks bei PCIe Transfers
export HSA_ENABLE_SDMA=0

# Startparameter:
# --reserve-vram 3 : Schützt 3 GB VRAM für den Desktop (GNOME/Wayland)
# --cache-ram 8 32 : Begrenzt Host-RAM-Caching (8 GB aktiv, 32 GB max), verhindert RAM-Überlastung
exec python main.py --reserve-vram 3 --cache-ram 8 32 --listen 0.0.0.0 --port 8188
