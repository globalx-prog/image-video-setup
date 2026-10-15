# 📚 Master-Inhaltsverzeichnis der Dokumentation
> **Projekt:** Bild- und Video-KI Setup mit AMD Radeon PRO W7800 (48 GB VRAM, ROCm 6.4)

Die Dokumentation ist thematisch und nach Komplexitätsgrad strukturiert:
- **01–09:** Grundlegende Themen (Hardware, Setup, Sicherheit, Speicher, Nodes & Benchmarks)
- **10–19:** Video-Kernmodelle & Regie-Workflows (MiniMax H3 & Wan Video)
- **20–29:** Filmproduktion, Automatisierung & Praxis-Drehbücher (Langfilm-Pipeline)
- **30–39:** Pareto-Optimierung, Qualitäts-Mastering & LoRA-Erweiterungen (High-End & Neueste Features)

---

## 🗂️ Übersicht aller Dokumente

### 🧱 Block 1: Grundlagen, Hardware & System-Architektur (01–09)
Grundlegendes Wissen über das Gesamtsystem, ROCm-Konfiguration, Sicherheit und Speicher:

| Datei | Titel / Thema | Kurzbeschreibung & Kerninhalt |
| :--- | :--- | :--- |
| [`01-handbuch-bild-und-video-ki.md`](01-handbuch-bild-und-video-ki.md) | **Gesamthandbuch Bild- & Video-KI** | Das große Basis-Handbuch: Hardware (AMD W7800), ROCm 6.4, Modell-Übersichten, ComfyUI-Grundlagen und Troubleshooting. |
| [`02-sicherheitsguide-ollama-comfyui.md`](02-sicherheitsguide-ollama-comfyui.md) | **Sicherheits- & Netzwerk-Guide** | Portfreigaben (8188, 11434), Docker, Tailscale-VPN, Firewall-Regeln und Schutz vor unbefugtem Netzwerkzugriff. |
| [`03-speicher-und-workflow-guide.md`](03-speicher-und-workflow-guide.md) | **Speicher- & Stabilitäts-Guide** | Vermeidung von Swap-Thrashing, VRAM-Reservierung (`--reserve-vram 3`), mmap-Nutzung und ROCm-Kernel-Tuning. |
| [`04-nodes-und-workflows.md`](04-nodes-und-workflows.md) | **ComfyUI Node-Katalog** | Detaillierte Dokumentation aller installierten Custom Nodes, Modell-Loader, Scheduler und Canvas-Bausteine. |
| [`05-bild-und-video-benchmark.md`](05-bild-und-video-benchmark.md) | **Modell- & Hardware-Benchmarks** | Ursprüngliche Baseline-Messwerte für SDXL, FLUX, Wan und MiniMax H3 im direkten Performance-Vergleich. |

---

### 🎬 Block 2: Video-Kernmodelle & Regie-Workflows (10–19)
Spezifische Anleitungen zur Steuerung der Videomodelle, Regie-Prompting und Audio:

| Datei | Titel / Thema | Kurzbeschreibung & Kerninhalt |
| :--- | :--- | :--- |
| [`10-leitfaden-idealer-minimax-workflow.md`](10-leitfaden-idealer-minimax-workflow.md) | **Idealer MiniMax H3 Workflow** | Schrittweiser Aufbau des Basis-Workflows: Modell-Laden (int8 convrot), Turbo-Switch, KSampler und Video-VAE. |
| [`11-film-produktions-leitfaden-settings.md`](11-film-produktions-leitfaden-settings.md) | **Film-Produktions-Leitfaden & Settings** | **Hauptreferenz:** 4-Spur-Regie (Style/Action/Camera/Audio), 2-Personen FaceDetailer Setup, YAML-Beispiele und Benchmark-Matrix. |
| [`12-anleitung-audio-in-wan.md`](12-anleitung-audio-in-wan.md) | **Audio-Synthese in Videomodellen** | Handhabung von nativer Audio-Generierung bei MiniMax H3 sowie nachträglicher Tonspursynchronisation bei Wan 2.1. |

---

### 🚀 Block 3: Langfilm-Pipeline & Automatisierung (20–29)
Vollautomatische Produktion zusammenhängender Filme aus Drehbüchern:

| Datei | Titel / Thema | Kurzbeschreibung & Kerninhalt |
| :--- | :--- | :--- |
| [`20-anleitung-minimax-h3-long-video-automation.md`](20-anleitung-minimax-h3-long-video-automation.md) | **Langfilm-Automation Pipeline** | Technische Dokumentation der Python-Engine (`auto_movie_maker.py`), Last-Frame-Handoff (`i2v`), Ref2V-Schnitt und Ollama-Storyzerlegung. |
| [`21-anleitung-kurzfilm-maus-minimax.md`](21-anleitung-kurzfilm-maus-minimax.md) | **Praxis-Case-Study: Detektivfilm** | Vollständiges Drehbuch-Beispiel (Maus-Detektiv) mit Storyboard, Prompts und Szenenfolgen zur Demonstration. |

---

### 🌟 Block 4: High-End Qualität, Pareto & LoRA-Erweiterungen (30–39)
Die neuesten und fortgeschrittensten Optimierungen für maximale Qualität in minimaler Rechenzeit:

| Datei | Titel / Thema | Kurzbeschreibung & Kerninhalt |
| :--- | :--- | :--- |
| [`30-pareto-optimierungs-status.md`](30-pareto-optimierungs-status.md) | **Pareto-Optimierung & VRAM-Guard** | Detaillierte Analyse des Sweet Spots (9.5/10 Qualität in 18 Min) und der 2-Stufen-Sicherheitsarchitektur gegen VRAM-Überläufe. |
| [`31-optimaler-qualitaets-ablauf-befehle.md`](31-optimaler-qualitaets-ablauf-befehle.md) | **Optimaler Qualitäts-Ablauf (Alle Befehle)** | Kompakte Schritt-für-Schritt Befehlsfolge: Pre-FaceDetailer, 8 Steps, 1080p Upscale, xfade-Schnitt und Soundtrack-Mastering. |
| [`32-empfohlene-video-loras.md`](32-empfohlene-video-loras.md) | **Empfohlene Video-LoRAs** | Online-Recherche von Civitai & HuggingFace: Top-LoRAs für Kinolicht, Drohnen-Kamerafahrten, 35mm-Korn, Hautporen & Speed. |
| [`33-amd-w7800-tuning-und-lueftersteuerung.md`](33-amd-w7800-tuning-und-lueftersteuerung.md) | **W7800 Hardware-Tuning & Lüfter** | Power-Limit (205W auf 230W), Profil 5 COMPUTE, DPM High und temperaturgeführte Blower-Lüfterkurve gegen Drosselung. |
| [`34-luefter-setups-und-kuehlprofile.md`](34-luefter-setups-und-kuehlprofile.md) | **Lüfter-Setups & Kühlprofile** | Umfassender Leitfaden: 5 Kühlprofile (Silent, Balanced, Sweet Spot 65%, Max 85%, Auto), udev-Regeln ohne sudo und systemd-Daemon. |
| [`35-ki-video-upscaling-und-post-processing.md`](35-ki-video-upscaling-und-post-processing.md) | **KI-Video-Upscaling (Real-ESRGAN)** | Vollständige Post-Processing Pipeline: Entkoppeltes FP16-Upscaling auf W7800 (<2 GB VRAM), Supersampling 1080p/4K, FFmpeg-Streaming. |
| [`36-film-regie-flow-logfile-und-swap-management.md`](36-film-regie-flow-logfile-und-swap-management.md) | **Film-Regie, Upscale-Verbindung & SWAP** | 3-Akt Dramaturgie gegen Ping-Pong-Cuts, automatische End-zu-End KI-Upscaling Pipeline, production.log & SWAP-Reclaim. |
| [`37-comfyui-performance-gui-tuning-und-fluessiges-arbeiten.md`](37-comfyui-performance-gui-tuning-und-fluessiges-arbeiten.md) | **ComfyUI Performance & GUI-Tuning** | Beseitigung von Canvas-Lag (Straight Links), History-Cleanup, Linux Swappiness, DPM High und VRAM-Warmstart. |
| [`38-perfekte-quellbild-vorbereitung-fuer-ki-video.md`](38-perfekte-quellbild-vorbereitung-fuer-ki-video.md) | **Perfekte Quellbild-Vorbereitung** | Bildausschnitt (Bust-Shot), Mimik, Licht, Freistellung, Pre-FaceDetailer (0.32 Denoise) & Dateiformate. |


