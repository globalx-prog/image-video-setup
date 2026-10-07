#!/bin/bash
# Startet ComfyUI (native AMD/ROCm). Port 8188 auf allen Interfaces,
# damit Open WebUI (Docker) über die Tailscale-IP zugreifen kann.
cd "$(dirname "$0")"
source comfy_env/bin/activate
cd ComfyUI
exec python main.py --reserve-vram 3 --listen 0.0.0.0 --port 8188
