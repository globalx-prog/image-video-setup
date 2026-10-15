# 🎨 ComfyUI Studio (Bild- & Video-KI Setup)

> **Hardware:** AMD Radeon PRO W7800 (48 GB VRAM) | 64 GB RAM | Ubuntu Linux  
> **Architektur:** Nativ ComfyUI (ROCm 6.4 / PyTorch 2.9) + Docker Open WebUI (via Tailscale)  
> **Port:** `8188` (gebunden an `0.0.0.0` für lokalen Zugriff & Tailscale `100.102.224.36:8188`)

---

## 🏛️ Architektur & Überblick

```text
                      [ Browser / Client ]
                        │              │
                        ▼              ▼
                 [ Open WebUI ]    [ ComfyUI Node-Editor ]
                 (Port 3000)       (Port 8188 / Service)
                        │              │
                        │ (HTTP API)   │ (ROCm 6.4 nativ)
                        └──────►───────┴────────► [ AMD Radeon PRO W7800 48GB VRAM ]
```

* **Warum nativ?** Docker Desktop auf Linux läuft in einer VM und sperrt den AMD ROCm Kernelzugriff (`/dev/kfd`). ComfyUI läuft daher direkt in einer optimierten Python-3.12-Umgebung (`comfy_env`).
* **Autostart:** Gekoppelt als Systemd-Benutzerdienst (`comfyui.service`).

---

## 📁 Verzeichnis-Struktur (NAS-Standard)

```text
image-video-setup/
├── configs/                     # Service- & Docker-Konfigurationen
│   ├── comfyui.service          # Systemd-Dienstvorlage
│   └── docker/                  # Optionale / historische Compose-Dateien
├── docs/                        # Vollständige, thematisch nummerierte Dokumentation
│   ├── 00-inhaltsverzeichnis-dokumentation.md # Master-Inhaltsverzeichnis aller Dokumente
│   ├── 01-handbuch-bild-und-video-ki.md     # Das Gesamthandbuch & System-Architektur
│   ├── 02-sicherheitsguide-ollama-comfyui.md# Crash-Forensik, Ports & Netzwerk-Schutz
│   ├── 03-speicher-und-workflow-guide.md    # VRAM-Management & ROCm-Kernel-Tuning
│   ├── 04-nodes-und-workflows.md            # Wichtige Nodes & Canvas-Referenz
│   ├── 05-bild-und-video-benchmark.md       # Benchmarks & Modell-Vergleiche
│   ├── 10-leitfaden-idealer-minimax-workflow.md # Idealer MiniMax H3 Workflow
│   ├── 11-film-produktions-leitfaden-settings.md# Regie, Multi-Charakter & Master-Settings
│   ├── 12-anleitung-audio-in-wan.md         # Audio-Integration & Muxing
│   ├── 20-anleitung-minimax-h3-long-video-automation.md # Vollautomatische Langfilm-Pipeline
│   ├── 21-anleitung-kurzfilm-maus-minimax.md# 15s Storyboard & Prompt-Guide (Case Study)
│   ├── 30-pareto-optimierungs-status.md     # Pareto-Prinzip & 2-Stufen VRAM-Crash-Schutz
│   ├── 31-optimaler-qualitaets-ablauf-befehle.md# Kompakter Master-Ablauf (alle Befehle)
│   └── 32-empfohlene-video-loras.md         # Top Online-LoRAs (Kamera, Licht, Filmkorn)
├── scripts/                     # Tägliche Steuerungs- & Wartungsbefehle
│   ├── start_comfyui.sh         # Server nativ mit ROCm-Optimierungen starten
│   ├── restart_comfyui.sh       # Smart-Restart mit VRAM-Bereinigung & Service-Check
│   └── free_vram.sh             # 1-Klick Speicherbereiniger (VRAM + RAM + Swap)
├── setup/                       # Nummerierte Setup- & Installationsskripte
│   ├── 01-install-comfyui-native.sh       # Basis-Installation (uv venv, PyTorch ROCm)
│   ├── 02-apply-amd-gpu-fixes.sh          # amdgpu Watchdog-Patch (60s Timeout)
│   ├── 03-setup-memory-and-swap-protection.sh # sysctl RAM-Reserve & Swap-Schutz
│   ├── 04-download-wan2.2-models.sh       # Wan 2.2 Model-Downloader
│   └── 05-download-flux2-models.sh        # FLUX.2 Dev Model-Downloader
└── ComfyUI/                     # Nativer ComfyUI Core & Modelle (300+ GB)
```

---

## 🚀 Tägliche Befehle (Spickzettel)

| Aktion | Befehl |
| :--- | :--- |
| **ComfyUI Status prüfen** | `systemctl --user status comfyui` |
| **ComfyUI Logs live ansehen** | `journalctl --user -u comfyui -f` |
| **ComfyUI neu starten & VRAM leeren** | `./scripts/restart_comfyui.sh` |
| **VRAM, RAM & Swap komplett leeren** | `./scripts/free_vram.sh` |
| **VRAM-Auslastung prüfen** | `rocm-smi --showmeminfo vram` |
| **Modelle auflisten** | `ls -lh ComfyUI/models/checkpoints/` |

> [!TIP]
> Für Rückwärtskompatibilität existieren Symlinks im Hauptverzeichnis: `./start_comfyui.sh`, `./restart_comfyui.sh` und `./free_vram.sh` funktionieren wie gewohnt!
