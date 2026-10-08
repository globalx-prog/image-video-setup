# 🎨 Das Kompletthandbuch: Lokales Bild- & Video-KI Setup
> **Hardware:** AMD Radeon PRO W7800 (48 GB VRAM) | 64 GB RAM | Linux Ubuntu  
> **Architektur:** Nativ ComfyUI (ROCm 6.4 / PyTorch 2.9) + Docker Open WebUI (via Tailscale)  
> **Stand:** Oktober 2026

---

## 📑 Inhaltsverzeichnis
- [🎨 Das Kompletthandbuch: Lokales Bild- \& Video-KI Setup](#-das-kompletthandbuch-lokales-bild---video-ki-setup)
  - [📑 Inhaltsverzeichnis](#-inhaltsverzeichnis)
  - [1. Architektur \& System-Überblick](#1-architektur--system-überblick)
    - [Warum läuft ComfyUI nativ und nicht im Docker?](#warum-läuft-comfyui-nativ-und-nicht-im-docker)
  - [2. Installierte Modelle \& Empfohlene Einsatzbereiche](#2-installierte-modelle--empfohlene-einsatzbereiche)
    - [A. Standalone Checkpoints (`ComfyUI/models/checkpoints/`)](#a-standalone-checkpoints-comfyuimodelscheckpoints)
    - [B. High-End Video Diffusion (`ComfyUI/models/`)](#b-high-end-video-diffusion-comfyuimodels)
    - [C. 🧩 Das Baukasten-Prinzip: Erklärung aller bisherigen Teilmodelle](#c--das-baukasten-prinzip-erklärung-aller-bisherigen-teilmodelle)
    - [D. 🎛️ Kreative Kontrolle & Bildbearbeitung (ControlNet & RMBG-2.0)](#d-️-kreative-kontrolle--bildbearbeitung-controlnet--rmbg-20)
    - [E. 🎬 Top 10 Freie VIDEO-Modelle (Text/Image-to-Video)](#e--top-10-freie-video-modelle-textimage-to-video)
    - [F. 🎨 Top 10 Freie BILD-Modelle (Text-to-Image)](#f--top-10-freie-bild-modelle-text-to-image)
    - [G. 🔍 Erkenntnisse aus den Leaderboards (Artificial Analysis & Arena.ai)](#g--erkenntnisse-aus-den-leaderboards-artificial-analysis--arenaai)
  - [3. Tägliche Nutzung: Schritt für Schritt](#3-tägliche-nutzung-schritt-für-schritt)
    - [A. Schnelle Bilder im Chat (Open WebUI)](#a-schnelle-bilder-im-chat-open-webui)
    - [B. Videos \& High-End Grafik (ComfyUI)](#b-videos--high-end-grafik-comfyui)
    - [C. ComfyUI ohne Frust verstehen ("Drag \& Drop"-Magie)](#c-comfyui-ohne-frust-verstehen-drag--drop-magie)
  - [4. Fehlerbehebung \& Praxiserkenntnisse](#4-fehlerbehebung--praxiserkenntnisse)
    - [A. Der "Error 400 (Bad Request)" in Open WebUI](#a-der-error-400-bad-request-in-open-webui)
    - [B. Das "Overcooking"-Problem: Warum FLUX.1 zwingend CFG 1.0 braucht](#b-das-overcooking-problem-warum-flux1-zwingend-cfg-10-braucht)
    - [C. Der "Size mismatch for shared.weight"-Fehler beim CLIPLoader](#c-der-size-mismatch-for-sharedweight-fehler-beim-cliploader)
    - [D. Der "not enough values to unpack (expected 5, got 3)" Fehler](#d-der-not-enough-values-to-unpack-expected-5-got-3-fehler)
    - [E. AMD ROCm vs. NVIDIA nvfp4 (Warum int8\_convrot nötig ist)](#e-amd-rocm-vs-nvidia-nvfp4-warum-int8_convrot-nötig-ist)
    - [F. Der "GPU Hang" \& Desktop-Reset bei langen Video-Renders (amdgpu Watchdog-Timeout)](#f-der-gpu-hang--desktop-reset-bei-langen-video-renders-amdgpu-watchdog-timeout)
  - [5. Modelle finden, testen \& neue Funktionen nachrüsten](#5-modelle-finden-testen--neue-funktionen-nachrüsten)
    - [A. Der ComfyUI-Manager (Der interne "App Store")](#a-der-comfyui-manager-der-interne-app-store)
    - [B. Manuell heruntergeladene Modelle ablegen](#b-manuell-heruntergeladene-modelle-ablegen)
  - [6. VRAM-Sicherheit \& Stabilitätsschutz (Freeze-Prävention)](#6-vram-sicherheit--stabilitätsschutz-freeze-prävention)
  - [7. Roadmap: Offene TODOs \& Optimierungen](#7-roadmap-offene-todos--optimierungen)
  - [8. Spickzettel: Wichtige Terminal-Befehle](#8-spickzettel-wichtige-terminal-befehle)

---

## 1. Architektur & System-Überblick

Um die volle Leistung deiner 48 GB AMD-Grafikkarte abzurufen, arbeitet das Setup zweigeteilt:

```
                      [ Browser / Client ]
                        │              │
                        ▼              ▼
                [ Open WebUI ]    [ ComfyUI Node-Editor ]
                (Port 3000)       (Port 8188 / Service)
                        │              │
                        │ (HTTP API)   │ (ROCm 6.4 nativ)
                        └──────►───────┴────────► [ AMD Radeon PRO W7800 48GB VRAM ]
```

### Warum läuft ComfyUI nativ und nicht im Docker?
* **Die Docker Desktop Limitation:** Docker Desktop auf Linux läuft in einer versteckten virtuellen Maschine (VM). Dadurch wird der direkte AMD-Treiberzugriff (`/dev/kfd`) blockiert.
* **Die native Lösung:** ComfyUI läuft über eine isolierte Python-3.12-Umgebung (`uv`) mit nativem ROCm 6.4 direkt auf dem Host. Es ist als User-Dienst (`comfyui.service`) gekoppelt und startet automatisch, sobald Docker Desktop läuft.
* **Open WebUI:** Greift über die Tailscale-IP (`http://100.102.224.36:8188/`) sicher auf ComfyUI zu.

---

## 2. Installierte Modelle & Empfohlene Einsatzbereiche

> 💡 **Ausführliches Benchmark-Ranking & Gesamtübersicht:** Siehe [BILD_UND_VIDEO_BENCHMARK_BEWERTUNG.md](BILD_UND_VIDEO_BENCHMARK_BEWERTUNG.md) für das vollständige Multi-Kriterien-Ranking aller 4 Kategorien (Bild, Video, Sprach-KI & ControlNets).

Alle Modelle sind heruntergeladen, verifiziert und in ComfyUI registriert:

### A. Standalone Checkpoints (`ComfyUI/models/checkpoints/`)
| Modell | Datei | Größe | Zweck & Besonderheit |
| :--- | :--- | :--- | :--- |
| **FLUX.1 [dev]** | `flux1-dev-fp8.safetensors` | 17.2 GB | **Platz 1 weltweit (Open Weights):** Höchste Schärfe, perfekte Haut/Augen, genaue Textdarstellung (20–28 Steps). |
| **FLUX.1 [schnell]** | `flux1-schnell-fp8.safetensors` | 17.0 GB | **Platz 2 weltweit:** Extrem schnell (nur 4 Steps). Perfekt für den Chat in Open WebUI. |
| **SD 3.5 Large** | `sd3.5_large_fp8_scaled.safetensors` | 14.9 GB | **Stability AI Flaggschiff (8B):** Starke Typografie, sehr flexibel in Stilen (Fotografie & Grafik). |
| **SDXL Base 1.0** | `sd_xl_base_1.0.safetensors` | 6.5 GB | **Open-Source-Standard:** Größtes Ökosystem für Community-Finetunes & LoRAs. |
| **LTX-Video 2B** | `ltx-video-2b-v0.9.1.safetensors` | 5.4 GB | **Echtzeit-Videomodell:** Schnelle 24fps Text-to-Video & Image-to-Video Clips. |
| **SVD-XT** | `svd_xt.safetensors` | 9.0 GB | **Image-to-Video:** Erstellt flüssige 25-Frame Kamerafahrten aus Standbildern. |
| *Kompatibilitäts-Link* | `model.safetensors` | Symlink | Zeigt auf `flux1-schnell-fp8.safetensors` (behebt Default-Fallback). |

### B. High-End Video Diffusion (`ComfyUI/models/`)
* **Wan 2.1 (14B) – Alibabas Spitzen-Videomodell (BF16 unkomprimiert):**
  * **Diffusion Model:** `models/diffusion_models/wan2.1_t2v_14B_bf16.safetensors` (28.5 GB)
  * **Text Encoder:** `models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` (6.7 GB)
  * **Video VAE:** `models/vae/wan_2.1_vae.safetensors` (254 MB)
  * **Fertiger Workflow:** `user/default/workflows/wan2.1_t2v.json` *(im Menü direkt ladbar!)*
  * *Eigenschaft:* Höchste physikalische Bewegungskonsistenz und Detailtiefe. Nutzt deine 48 GB VRAM voll aus.
* **MiniMax-H3 (Hailuo 03) – Video- & Native Audio-Generierung (AMD ROCm / HIP Edition):**
  * **Diffusion Core:** `models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` (19.5 GB)
  * **Text Encoder (AMD-nativ):** `models/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (25.3 GB)
  * **Video VAE:** `models/vae/minimax_h3_video_vae_int8_convrot.safetensors` (2.6 GB)
  * **Audio VAE:** `models/vae/minimax_h3_audio_vae_fp32.safetensors` (580 MB)
  * **Turbo LoRA (8-Steps):** `models/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (1.8 GB)
  * **Beispiel-Eingabebild:** `input/transparent_rgb_gaming_mouse.png` (1.3 MB)
  * **Fertige Workflows:** `user/default/workflows/video_minimax_h3_i2v_amd.json` & `video_minimax_h3_t2v_amd.json`
  * *Wichtige AMD-Besonderheit:* Standard-Workflows verlinken oft auf NVIDIA-`nvfp4`. Auf AMD ROCm muss zwingend die `int8_convrot`-Variante gewählt werden (per Symlink und Workflow-Preset automatisch abgesichert).

Aufgaben unterscheiden:

🔊 Die große Besonderheit von MiniMax-H3: Native Audio-Generierung

- MiniMax-H3 erzeugt Video UND passenden Sound gleichzeitig (daher der Eintrag audio_vae). Wenn du Videos generieren willst, die direkt passende Geräusche, Sprache oder Hintergrund-Soundtracks haben, ist MiniMax-H3 eines der wenigen Modelle, die das nativ können.
- Bei cineastischer Bewegung und allgemeiner Video-Qualität rangiert MiniMax in den Arena-Leaderboards ganz oben bei den Top-Modellen.

⚖️ Der direkte Vergleich mit deinen Modellen:

Gegen Wan 2.1 (14B) (das du bereits installiert hast):
- Wan 2.1: Gewinnt bei reiner Bildqualität, Texttreue und physikalischer Konsistenz (Bewegung von Objekten, Kleidung, Flüssigkeiten). Wan 2.1 gilt aktuell in der Open-Source-Community als der Maßstab für visuelle Qualität. Wan erzeugt allerdings standardmäßig erst einmal nur Video ohne Audio.
- MiniMax-H3: Hat den Vorteil, dass Audio direkt mitgerendert wird. Visuell sind Wan 2.1 und MiniMax-H3 auf Augenhöhe.

Gegen LTX-Video 2B (das du bereits installiert hast):
- MiniMax-H3 ist qualitativ spürbar detaillierter und filmreifer als LTX-Video.
- LTX-Video ist dafür 5-mal schneller und extrem leichtgewichtig.

### C. 🧩 Das Baukasten-Prinzip: Erklärung aller bisherigen Teilmodelle

Warum gibt es neben Standalone-Checkpoints (wie FLUX oder SDXL) so viele separate Ordner wie `diffusion_models`, `text_encoders`, `vae` und `loras`?

#### 1. Der Unterschied: Monolith vs. Baukasten
* **Monolithische Checkpoints (`models/checkpoints/`):** Klassische Modelle packen alles (Text-Verständnis, Diffusions-Kern und Bild-Dekodierer) in eine einzige große Datei. Das ist bequem, aber unflexibel und verschwendet VRAM, da alles gleichzeitig im Speicher gehalten werden muss.
* **Modulare Teilmodelle (Diffusers-Architektur):** Moderne High-End Modelle wie **Wan 2.1**, **MiniMax-H3** und professionelle FLUX-Pipelines trennen die drei Kernaufgaben strikt voneinander:
  1. **Text Encoder (Das Gehirn für Sprache):** Übersetzt deinen englischen oder deutschen Prompt in hochdimensionale mathematische Einbettungen (Embeddings). Läuft nur am Anfang des Renderings und kann danach sofort aus dem VRAM entladen werden!
  2. **Diffusion Model / DiT (Der Bild-/Video-Maler):** Das eigentliche gigantische neuronale Netz, das aus reinem Rauschen Schritt für Schritt die Bewegung und Details formt.
  3. **VAE (Der Übersetzer von Latent zu Pixeln):** Arbeitet nicht im teuren Pixelraum, sondern komprimiert Bilder/Videos um den Faktor 8x bis 16x in den "Latent Space". Erst ganz am Schluss wandelt der VAE-Decoder die Daten in ein sichtbares PNG oder MP4 um.

#### 2. Detaillierte Bestandsaufnahme aller installierten Teilmodelle:

| Kategorie & Ordner | Installierte Datei | Größe | Funktion & Zusammenspiel |
| :--- | :--- | :--- | :--- |
| **Diffusion Cores**<br>`models/diffusion_models/` | `wan2.1_t2v_14B_bf16.safetensors` | 27.2 GB | **Alibaba Wan 2.1 (14B):** Unkomprimierter DiT in voller BF16-Präzision. Spezialisiert auf physikalisch korrekte Simulation von Licht, Kleidung, Wasser und Bewegung. |
| | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 19.5 GB | **MiniMax Hailuo-03 Core:** AMD ROCm-optimierter Kern, der simultan Video- und Audio-Latents generiert. |
| **Text Encoders**<br>`models/text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3 GB | **Google UMT5-XXL:** Universeller multilingualer Sprach-Encoder für Wan 2.1 (versteht hochkomplexe, verschachtelte Prompts). |
| | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 25.3 GB | **Qwen3-VL (32B):** Multimodales Großmodell als Text- und Bild-Interpreter für MiniMax-H3 (AMD-optimierte Rotationstensor-Version). |
| **Variational Autoencoder**<br>`models/vae/` | `wan_2.1_vae.safetensors` | 243 MB | **Wan 3D VAE:** Temporaler Video-Decoder, der flüssige Frame-Übergänge ohne Flimmern gewährleistet. |
| | `minimax_h3_video_vae_int8_convrot.safetensors` | 2.6 GB | **MiniMax Video VAE:** Dekodiert die visuellen Farb- und Kontrast-Informationen. |
| | `minimax_h3_audio_vae_fp32.safetensors` | 578 MB | **MiniMax Audio VAE:** Einzigartiger Audio-Synthesizer, der die latenten Sound-Tokens in eine hörbare MP3/WAV-Tonspur umrechnet. |
| **LoRAs & Adapter**<br>`models/loras/` | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 1.8 GB | **8-Step Turbo LoRA:** Reduziert die Renderzeit von MiniMax-H3 drastisch von 50 Schritten auf nur 8 Schritte bei fast identischer Qualität. |
| | `FireRed-Image-Edit-1.0-Lightning-8steps-v1.0.safetensors` | 811 MB | **Image-Edit Lightning LoRA:** Ermöglicht gezielte Bildanpassungen und Stylings mit minimaler Schrittzahl. |
| **Upscaler**<br>`models/upscale_models/` | `R-ESRGAN 4x+.pth` | 64 MB | **Real-ESRGAN 4x+:** Industriestandard für neuronales 4K-Upscaling von Gesichtern, Texturen und feinen Details. |

---

### D. 🎛️ Kreative Kontrolle & Bildbearbeitung (ControlNet & RMBG-2.0)

Um nicht nur "Zufallsbilder per Text" zu generieren, sondern die volle Regie über Haltung, Tiefenschärfe, Kanten und Freistellen zu übernehmen:

#### 1. Hintergrund-Entfernung & Freistellen: RMBG-2.0 (`models/background_removal/`)
* **Installierte Modelle:** `RMBG-2.0.safetensors` & Symlink `birefnet.safetensors` (844 MB)
* **Basis & Technologie:** Entwickelt von BRIA AI auf Basis modernster BiRefNet-Architektur.
* **Leistung & Stärke:**
  * Entfernt Hintergründe in Bruchteilen einer Sekunde mit Sub-Pixel-Genauigkeit.
  * Erkennt feinste Haarsträhnen, transparente Gläser, Schmuck und komplexe Produktkanten ohne Fransenkanten.
  * Liefert sowohl ein **transparentes RGBA-Bild** als auch eine saubere **Schwarz-Weiß-Maske** für Inpainting-Workflows.
* **Einsatz in ComfyUI:**
  * Nativer Node: `Load Background Removal Model` ➔ `Remove Background`.

#### 2. All-in-One ControlNet Union Modelle (`models/controlnet/`)
Statt für jede Kontrollmethode (Pose, Tiefe, Kante) eine eigene 2-GB-Datei zu laden, nutzen wir moderne **Union-Modelle** (alle Kontrollarten in einer einzigen Datei):

| Modell | Datei | Größe | Unterstützte Modi in 1 Modell |
| :--- | :--- | :--- | :--- |
| **SDXL ControlNet Union ProMax** | `controlnet-union-sdxl-1.0-promax.safetensors` | 2.5 GB | **10+ Modi:** OpenPose (Körperhaltung), Depth (3D-Tiefe), Canny & Lineart (Kanten/Zeichnungen), Scribble (Handskizzen), Tile (Upscale/Detailer), Normal Map, Segment. |
| **FLUX.1-dev ControlNet Union Pro** | `flux1-dev-controlnet-union-pro.safetensors` | 6.6 GB | **7 Modi:** Canny, Depth, Pose, Tile, Blur, Gray, Low-Quality speziell trainiert für die FLUX.1 [dev] Transformer-Architektur. |

* **Typische Praxisszenarien:**
  * **Exakte Körperhaltung:** Ein Foto einer Person als Pose vorgeben ➔ FLUX generiert deinen Charakter in exakt derselben Pose.
  * **Produktplatzierung & 3D-Tiefe:** Tiefenkarte (Depth) eines Zimmers oder Tisches vorgeben ➔ Neues Objekt fügt sich perfekt perspektivisch ein.
  * **Logo & Skizzen-Rendering:** Handzeichnung per Canny/Lineart einspeisen ➔ Modell malt fotorealistisches Bild exakt entlang der Linien.
* **Empfohlene Node-Einstellungen:**
  * Node: `Apply ControlNet` oder `Apply ControlNet (Advanced)`.
  * Stärke (`strength`): **0.6 bis 0.8** (ideal für natürliche Integration, bei 1.0 wirkt das Ergebnis manchmal übersteuert).

---

### E. 🎬 Top 10 Freie VIDEO-Modelle (Text/Image-to-Video)

| Rang | Modell | Entwickler | Größe / VRAM | Wichtigste Eigenschaften | Umsetzung / Eignung | Status Lokal |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **HunyuanVideo** | Tencent | ~24 GB (BF16) / ~14 GB (FP8) | Höchster Open-Source Elo; filmreife Kameraführung & Gesichtsdetails. | ComfyUI (HunyuanWrapper) | Möglich (Download) |
| **2** | **Wan 2.1 (T2V/I2V)** | Alibaba | ~14 GB (14B) / ~3.2 GB (1.3B) | State-of-the-Art Physik, extrem komplexe Bewegungsabläufe. | ComfyUI Custom Node | **Bereit ✅ (14B BF16)** |
| **3** | **LTX-Video 2B** | Lightricks | ~5.4 GB | Ultraschneller DiT, 24fps Text-to-Video und Image-to-Video. | ComfyUI Checkpoint | **Bereit ✅** |
| **4** | **Mochi 1** | Genmo | ~38 GB (BF16) / ~19 GB (FP8) | Sehr flüssige 30fps Bewegungen, profitiert maximal von 48 GB VRAM. | ComfyUI MochiWrapper | Möglich (Download) |
| **5** | **CogVideoX-5B** | THUDM | ~10 GB | Cineastischer Look, starke Tiefenwirkung und Dynamik. | ComfyUI CogVideo-Node | Möglich (Download) |
| **6** | **Stable Video Diffusion XT** | Stability AI | ~9.0 GB | Der etablierte Standard für 25-Frame Image-to-Video Animationen. | ComfyUI Checkpoint | **Bereit ✅** |
| **7** | **CogVideoX-2B** | THUDM | ~4.5 GB | Leichtgewichtig, ideal für schnelles Prototyping von Videoclips. | ComfyUI CogVideo-Node | Möglich (Download) |
| **8** | **AnimateDiff (SDXL)** | Guoyww et al. | ~3 GB (Motion Modul) | Verwandelt jedes SDXL-Bildmodell in flüssige Kurzvideos via LoRAs. | ComfyUI VideoHelperSuite | Möglich (Download) |
| **9** | **ConsistI2V** | PKU / Tsinghua | ~8 GB | Spezialisiert auf extreme Bildkonsistenz von Start- bis Endframe. | ComfyUI / Python | Möglich (Download) |
| **10** | **DynamiCrafter** | CUHK / Tencent | ~7 GB | Starke Image-to-Video Animationen mit steuerbarer Kameradynamik. | ComfyUI DynamiCrafter | Möglich (Download) |
| *Top* | **MiniMax-H3 (Hailuo 03)** | MiniMax | ~19.5 GB (int8_convrot) | State-of-the-Art Video mit nativer Sound-/Audio-Generierung. | ComfyUI Diffusers/HIP | **Bereit ✅** |

### F. 🎨 Top 10 Freie BILD-Modelle (Text-to-Image)

| Rang | Modell | Entwickler | Größe / Format | Wichtigste Eigenschaften | Umsetzung / Eignung | Status Lokal |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **FLUX.1 [dev]** | Black Forest Labs | ~23 GB (BF16) / ~17 GB (FP8) | Höchster Open-Source Elo, fotorealistische Haut, perfekte Textdarstellung. | ComfyUI Checkpoint | **Bereit ✅ (FP8)** |
| **2** | **FLUX.1 [schnell]** | Black Forest Labs | ~17 GB (FP8) | Extrem schnell (nur 4 Steps), fast identische Qualität wie [dev]. | ComfyUI / Open WebUI | **Bereit ✅** |
| **3** | **SD 3.5 Large** | Stability AI | ~16 GB (FP16) / ~15 GB (FP8) | 8B Parameter, starke typografische Fähigkeiten, flexibler Stil. | ComfyUI Checkpoint | **Bereit ✅ (FP8)** |
| **4** | **SD 3.5 Medium** | Stability AI | ~5 GB (FP16) | Ausbalanciert für schnelle Generierungen bei gutem Prompt-Verständnis. | ComfyUI Checkpoint | Möglich (Download) |
| **5** | **SDXL Base 1.0** | Stability AI | ~6.5 GB (FP16) | Riesiges Ökosystem, tausende Community-Finetunes & LoRAs. | ComfyUI / Open WebUI | **Bereit ✅** |
| **6** | **Pony Diffusion V6 XL** | Community (Astrite) | ~6.5 GB | Unübertroffen für Comic, Anime, Styling und anatomische Genauigkeit. | ComfyUI Checkpoint | Möglich (Download) |
| **7** | **Juggernaut XL (v9/v10)** | RunDiffusion | ~6.5 GB | Bester SDXL-Finetune für cineastische Fotos & Landschaftsfotografie. | ComfyUI Checkpoint | Möglich (Download) |
| **8** | **Kolors** | Kuaishou | ~14 GB | Starke Textverständnis-Engine (GLM-basiert), zweisprachig (EN/ZH). | ComfyUI / Diffusers | Möglich (Download) |
| **9** | **SDXL Turbo** | Stability AI | ~6.5 GB | 1-Step Echtzeit-Bildgenerierung für Live-Workflows. | ComfyUI Checkpoint | Möglich (Download) |
| **10** | **PixArt-Sigma** | PixArt Alpha | ~3.5 GB | Sehr kompakt, 4K-fähig, exzellente Schärfe bei geringem Speicherbedarf. | ComfyUI Checkpoint | Möglich (Download) |

### G. 🔍 Erkenntnisse aus den Leaderboards (Artificial Analysis & Arena.ai)

#### Text-to-Image:
* **Proprietäre Spitzenreiter:** Recraft V3, Midjourney v6.1 und DALL-E 3 führen die Elo-Rankings bei reinen Cloud-Diensten an.
* **Beste freie / Open-Weights Modelle:** **FLUX.1 [dev]** und **FLUX.1 [schnell]** (Black Forest Labs) dominieren das Open-Weights-Ranking unangefochten mit dem höchsten Elo-Score aller freien Modelle. Dahinter folgen Stable Diffusion 3.5 Large und SDXL Turbo/Base.
* **Gibt es noch bessere als FLUX?** Unter den freien Modellen **nein** – FLUX.1 ist aktuell die absolute Referenz für Prompt-Treue und Typografie.

#### Text-to-Video / Image-to-Video:
* **Proprietäre Spitzenreiter:** Runway Gen-3 Alpha, Kling 1.5, Luma Dream Machine und Sora.
* **Beste freie / Open-Weights Modelle:**
  * **HunyuanVideo (Tencent):** Führt das Open-Source-Ranking für fotorealistische Gesichter und lange, konsistente Clips an.
  * **Wan 2.1 (Alibaba):** Hervorragende physikalische Bewegung und Konsistenz (*lokal mit 14B BF16 installiert*).
  * **MiniMax-H3 (Hailuo 03):** Eines der stärksten Modelle weltweit mit nativer Audio-Generierung (*lokal installiert*).
  * **LTX-Video (Lightricks):** Schnellster Diffusion-Transformer für Echtzeit-nahe Videoclips (*lokal installiert*).
  * **Mochi 1 (Genmo):** Exzellente, flüssige Animationen (benötigt extrem viel VRAM – perfekt für 48 GB).
  * **SVD-XT (Stability AI):** Der robuste Klassiker für Image-to-Video (*lokal installiert*).

---

## 3. Tägliche Nutzung: Schritt für Schritt

### A. Schnelle Bilder im Chat (Open WebUI)
*Ideal für Brainstorming, Illustrationen und schnelle Antworten.*

1. Öffne Open WebUI im Browser: `http://localhost:3000` (oder unterwegs via Cloudflare: `https://openwebui.nas-clemens.de`).
2. **Einmalige Einrichtung (Admin-Account):**
   * Gehe auf **Admin-Panel ➔ Einstellungen ➔ Bilder**.
   * **Engine:** `comfyui`
   * **ComfyUI Base URL:** `http://100.102.224.36:8188/`
   * **Modell:** Wähle `flux1-schnell-fp8.safetensors` (oder `flux1-dev-fp8.safetensors`).
   * Klicke auf **Speichern**.
3. **Im Chat:**
   * Schreibe einfach deinen Prompt (z. B. *"Ein fotorealistischer Pelikan auf einem Rennrad"*).
   * Das Bild wird binnen weniger Sekunden auf der AMD GPU gerendert und direkt im Chatverlauf angezeigt.

---

### B. Videos & High-End Grafik (ComfyUI)
*Ideal für Animationen, MP4-Videoexport, 4K-Upscaling und komplexe Bildbearbeitung.*

1. Öffne im Browser: **`http://localhost:8188`**.
2. **Schnellstart für Checkpoints (FLUX, SDXL, LTX-Video, SVD):**
   * Im Kasten (Node) **`Load Checkpoint`** das gewünschte Modell im Dropdown auswählen.
   * Prompt in die Textbox eintragen.
   * Rechts im Menü auf **"Queue Prompt"** klicken.
3. **Videos mit Wan 2.1 (14B) ohne Kabelsalat:**
   * Klicke oben rechts auf **"Workflows" ➔ `wan2.1_t2v.json`**.
   * Der Workflow ist fertig verdrahtet:
     * `UNETLoader`: `wan2.1_t2v_14B_bf16.safetensors`
     * `CLIPLoader`: `umt5_xxl_fp8_e4m3fn_scaled.safetensors` mit Typ `wan`
     * `VAELoader`: `wan_2.1_vae.safetensors`
   * Prompt eingeben und auf **"Queue Prompt"** klicken. Die Ausgabe wird über **`Video Combine`** direkt als `.mp4` gespeichert.
4. **Videos & Audio mit MiniMax-H3 (AMD-Version):**
   * In ComfyUI auf **"Workflows" ➔ `video_minimax_h3_i2v_amd.json`** (Image-to-Video) oder **`video_minimax_h3_t2v_amd.json`** (Text-to-Video) klicken.
   * **Modell-Dropdowns prüfen:**
     * `clip_name`: `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` *(nicht nvfp4!)*
     * `vae_name`: `minimax_h3_video_vae_int8_convrot.safetensors`
     * `audio_vae`: `minimax_h3_audio_vae_fp32.safetensors`
     * `diffusion_model`: `minimax_h3_fl2va_pruned_int8_convrot.safetensors`
   * Der Workflow erzeugt synchronisiertes Video inklusive Soundtrack/Audiotrack!

---

### C. ComfyUI ohne Frust verstehen ("Drag & Drop"-Magie)
ComfyUI wirkt wie ein unübersichtlicher Kabelsalat. **Du musst diese Kabel im Alltag fast nie selbst stecken!**

**Der Profil-Trick:**
1. Gehe auf Plattformen wie [Civitai.com](https://civitai.com) oder [OpenArt.ai / Workflows](https://openart.ai/workflows).
2. Lade dir ein Bild oder Video herunter, dessen Stil oder Bewegung dir gefällt.
3. Ziehe die Bild-/Videodatei per **Drag & Drop direkt in dein offenes ComfyUI-Browserfenster**.
4. **Magie:** ComfyUI liest die versteckten Metadaten der Datei und baut **in einer Sekunde alle Boxen, Kabel und Sampler exakt so auf**, wie der Profi-Ersteller sie eingerichtet hat.
5. Du musst nur noch den Prompt-Text ändern und auf **"Queue Prompt"** drücken!

---

## 4. Fehlerbehebung & Praxiserkenntnisse

### A. Der "Error 400 (Bad Request)" in Open WebUI
* **Symptom:** Open WebUI meldet beim Generieren: `Serverfehler (400): Error while queuing prompt`.
* **Ursache:** In den ComfyUI-Logs (`journalctl --user -u comfyui`) stand:
  `Value not in list: ckpt_name: 'model.safetensors' not in [...]`  
  Open WebUI hat den Standard-Platzhalternamen `model.safetensors` angefragt, der nicht existierte.
* **Lösung:**
  1. Auf Dateisystemebene wurde ein Symlink `model.safetensors -> flux1-schnell-fp8.safetensors` eingerichtet.
  2. In Open WebUI unter *Admin ➔ Einstellungen ➔ Bilder* muss explizit der tatsächliche Dateiname (z. B. `flux1-schnell-fp8.safetensors` oder `flux1-dev-fp8.safetensors`) eingetragen und gespeichert werden.

### B. Das "Overcooking"-Problem: Warum FLUX.1 zwingend CFG 1.0 braucht
* **Symptom:** Generierte Bilder (z. B. im Chat) wirken radioaktiv grell, neon-pink/lila übersättigt oder wie verbrannt.
* **Ursache:** Der Parameter `CFG (Guidance Scale)` stand auf `8.0` (Standardwert für alte Modelle wie SD 1.5).
  * FLUX.1 ist ein modernes **Flow-Matching-Modell** (Rectified Flow). Es benötigt kein künstliches CFG, um dem Prompt exakt zu folgen.
  * Bei CFG `8.0` multipliziert der Sampler Kontraste und Sättigung um das Achtfache ("Overcooking").
* **Lösung:**
  * **CFG Scale fest auf `1.0` stellen!** (100% Original-Rechnung ohne Übersteuerung).
  * **Geschwindigkeitsbonus:** Bei CFG 1.0 entfällt der negative Sampler-Schritt (`batch_size * 1` statt `batch_size * 2`). Die Generierung ist exakt **doppelt so schnell** (nur ca. 3–5 Sekunden für 1024×1024 mit FLUX [schnell] auf der Radeon PRO W7800).

### C. Der "Size mismatch for shared.weight"-Fehler beim CLIPLoader
* **Symptom:** Workflow bricht nach 3 Sekunden ab mit:
  `Error(s) in loading state_dict for T5: size mismatch for shared.weight: copying a param with shape torch.Size([256384, 4096]) from checkpoint, the shape in current model is torch.Size([32128, 4096]).`
* **Ursache:** Im Kasten **`CLIPLoader`** ist zwar der Text-Encoder für Wan 2.1 (`umt5_xxl_fp8_e4m3fn_scaled.safetensors`) gewählt, aber das Dropdown **`type`** darunter steht fälschlicherweise auf `lumina2`, `sd3` oder Standard.
  * Standard-T5 (z. B. Lumina) hat ein Vokabular von **32.128** Tokens.
  * Wan 2.1 UMT5-XXL hat ein Vokabular von **256.384** Tokens.
  * Die Matrizen passen nicht zusammen.
* **Lösung:** Im Node **`CLIPLoader`** das Dropdown **`type`** zwingend auf **`wan`** einstellen!

### D. Der "not enough values to unpack (expected 5, got 3)" Fehler
* **Symptom:** Workflow bricht beim `SamplerCustomAdvanced` ab mit:
  `ValueError: not enough values to unpack (expected 5, got 3)`.
* **Ursache:** Mischen von Video- und Bildkomponenten in einem Workflow:
  * Das Videomodell **Wan 2.1** erwartet einen **5D-Video-Tensor** (`[Batch, Channel, Frames, Höhe, Breite]`).
  * Wenn im Node `UNETLoader` noch versehentlich `wan2.1` ausgewählt ist, aber der Workflow von einem 2D-Bild-Latent (`EmptySD3LatentImage`) oder einem MiniMax-H3-Latent (gepackter 3D-NestedTensor) gefüttert wird, kann Wan die Dimensionen nicht entpacken.
* **Lösung:**
  * Immer aufeinander abgestimmte Workflows nutzen.
  * Für Wan 2.1: Die Vorlage `wan2.1_t2v.json` nutzen (mit `EmptyHunyuanLatentVideo` / Wan-Latents).
  * Für MiniMax-H3: Im `UNETLoader` immer das echte MiniMax-Modell (`minimax_h3_fl2va_pruned_int8_convrot.safetensors`) auswählen, nicht Wan!

### E. AMD ROCm vs. NVIDIA nvfp4 (Warum int8_convrot nötig ist)
* **Problem:** Viele offizielle Vorlagen von Comfy-Org für MiniMax-H3 referenzieren standardmäßig `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`. Das Format `nvfp4` ist ein proprietäres Tensor-Format für neuere NVIDIA-Karten (RTX 40er / Blackwell). Auf AMD ROCm schlägt der Kernel fehl oder fällt quälend langsam auf die CPU zurück.
* **Lösung:**
  * Auf AMD-Hardware muss immer die Variante **`int8_convrot`** geladen werden:
    * Text-Encoder: `qwen3vl_32b_minimax_h3_int8_convrot.safetensors`
    * Diffusion-Core: `minimax_h3_fl2va_pruned_int8_convrot.safetensors`
  * **Absicherung per Symlink:** Ein Symlink `models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors -> qwen3vl_32b_minimax_h3_int8_convrot.safetensors` leitet auch unbedarft importierte Community-Workflows automatisch auf den AMD-Kern um.

### F. Der "GPU Hang" & Desktop-Reset bei langen Video-Renders (amdgpu Watchdog-Timeout)
* **Symptom:** Ein Video-Workflow (z. B. Wan 2.1 14B) rendert viele Minuten völlig normal (z. B. bis Schritt 15/30). Plötzlich wird der Bildschirm schwarz, ComfyUI bricht mit `HW Exception: GPU Hang` ab und der Benutzer wird auf den Ubuntu-Anmeldebildschirm (GDM) zurückgeworfen.
* **Ursache:** 
  1. Deine AMD Radeon PRO W7800 ist die **einzige GPU im System** und berechnet gleichzeitig das KI-Video und den Wayland-Desktop.
  2. Wan 2.1 (14B BF16) benötigt ca. **30 Sekunden pro Rechenschritt**.
  3. Wenn währenddessen der Webbrowser (Firefox) Bildschirminhalte rendert, versucht er Grafikbefehle auf `ring gfx_0.0.0` auszuführen.
  4. Der Standard-Watchdog des Linux AMD-Treibers (`queue_preemption_timeout_ms = 9000`) wartet jedoch nur **9 Sekunden**. Da der 30s-Schritt die GPU noch voll beansprucht, vermutet der Treiber fälschlicherweise einen Hardware-Freeze und löst einen panischen `MODE1 GPU-Reset` aus.
* **Dauerhafte Lösung:**
  1. **AMD-Treiber-Timeout auf 60s erhöhen:**
     ```bash
     sudo /home/clemi/Projekte/LLM/image-video-setup/apply_amd_gpu_fixes.sh
     ```
     *(Setzt `lockup_timeout` und `queue_preemption_timeout_ms` auf 60.000 ms in `/etc/modprobe.d/amdgpu-timeout.conf` und baut das initramfs neu. Nach Reboot aktiv.)*
  2. **ComfyUI RAM- & SDMA-Optimierungen:** In [`start_comfyui.sh`](file:///home/clemi/Projekte/LLM/image-video-setup/start_comfyui.sh) sind `HSA_ENABLE_SDMA=0` (verhindert PCIe-SDMA-Hangs) sowie `--cache-ram 8 32` (schützt vor Host-RAM-Erschöpfung) fest hinterlegt.
  3. **Browser während 10-Minuten-Renders schonen:** Hardwarebeschleunigung in Firefox bei Bedarf drosseln oder den ComfyUI-Tab nicht im Vordergrund animieren lassen.

---

## 5. Modelle finden, testen & neue Funktionen nachrüsten

### A. Der ComfyUI-Manager (Der interne "App Store")
Rechts unten in ComfyUI findest du den Button **"Manager"**:
* **"Install Models":** Durchsuche eine riesige Bibliothek nach neuen Modellen, LoRAs und Upscalern. Ein Klick auf *Install* lädt die Datei direkt in das richtige Verzeichnis.
* **"Install Custom Nodes":** Neue Funktionen nachrüsten (z. B. Gesichter tauschen mit *ReActor*, Detailverbesserer mit *Impact Pack*).
* **"Install Missing Custom Nodes":** Wenn du einen fremden Workflow per Drag & Drop importierst und rote Boxen siehst, klicke hierauf – fehlende Module werden automatisch nachgeladen.

### B. Manuell heruntergeladene Modelle ablegen
Falls du Dateien von Hugging Face oder Civitai manuell lädst, gehören sie in diese Ordner:
* **Komplette Checkpoints:** `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints/`
* **Modulare Diffusionsmodelle (z. B. Wan):** `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/diffusion_models/`
* **LoRAs (Stile & Charaktere):** `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/loras/`
* **Upscaler (4K/8K KI-Skalierung):** `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/upscale_models/`

*Tipp:* Nach dem Hinzufügen einer Datei in ComfyUI rechts im Menü auf **"Refresh"** klicken.

---

## 6. VRAM-Sicherheit & Stabilitätsschutz (Freeze-Prävention)

> 📖 **Ausführlicher Leitfaden:** Siehe das dedizierte Handbuch [**`SICHERHEITSGUIDE_OLLAMA_COMFYUI.md`**](file:///home/clemi/Projekte/LLM/image-video-setup/SICHERHEITSGUIDE_OLLAMA_COMFYUI.md).

Dein Rechner besitzt **48 GB VRAM**, **64 GB System-RAM** und **36 GB Swap**. Dennoch ist Vorsicht geboten, wenn Sprachmodelle (Ollama) und Bild-/Videomodelle (ComfyUI) gleichzeitig laufen:

### Das Kernproblem (Ursache für GPU-Freezes):
1. **Ollama und ComfyUI wissen nichts voneinander:**  
   Wenn Ollama ein 30–35 GB Modell im Speicher hält (`qwen3.8-35b`, `artemis-31b`, `qwen3-coder`) und parallel ComfyUI gestartet wird (FLUX: 18 GB / Wan: 35 GB), fordern beide zusammen **über 55 GB VRAM** an!
2. **Die Folge auf AMD ROCm:**  
   Der Kernel versucht, VRAM über PCIe in den RAM auszulagern (SVM Page-Migration). Die SDMA-Engine der GPU läuft in ein Hardware-Timeout (`Fence fallback timer expired on ring sdma0`), und der gesamte Desktop friert ein!

### Die 3 Schutz-Regeln:
1. **Chat & Bild parallel (Open WebUI):**  
   * **Entweder** kompaktes LLM (`qwen3.8-27b-q4`, ~18 GB) + **FLUX.1 schnell** (18 GB) = **36 GB / 45 GB (100% sicher)**.
   * **Oder** großes LLM (35B, ~35 GB) + **SDXL Base** (7,5 GB) = **42,5 GB / 45 GB (Sicher)**.
2. **High-End Video (Wan 2.1 / MiniMax-H3):**  
   * Diese Modelle brauchen **35 GB VRAM ganz für sich allein**!
   * **Pflicht:** Vor dem Starten eines Video-Workflows den VRAM kurz freiräumen:
     ```bash
     /home/clemi/Projekte/LLM/image-video-setup/free_vram.sh
     ```
3. **Automatischer Desktop-Schutzwall:**  
   * In `start_comfyui.sh` ist `--reserve-vram 3` hinterlegt. ComfyUI lässt der Benutzeroberfläche (Wayland/Xwayland) immer mindestens 3 GB Puffer frei, um Systemabstürze zu verhindern.

---

## 7. Roadmap: Offene TODOs & Optimierungen

- [x] ComfyUI ROCm Nativ-Setup mit PyTorch 2.9 & AMD GPU-Erkennung
- [x] Open WebUI Anbindung via Tailscale-IP & Docker Compose
- [x] FLUX.1 Schnell & FLUX.1 Dev einrichten
- [x] SD 3.5 Large & SDXL Base einrichten
- [x] LTX-Video 2B & SVD-XT einrichten
- [x] Wan 2.1 14B (BF16 Diffusion + Text Encoder + VAE) bereitstellen
- [x] Fehler 400 Fallback-Symlink (`model.safetensors`) anlegen
- [x] **Open WebUI:** Im Admin-Panel `flux1-schnell-fp8.safetensors` oder `flux1-dev-fp8.safetensors` final als Modell speichern und Test-Generierung prüfen.
- [x] **Firewall:** Port 8188 mit UFW absichern (nur Localhost & Tailscale erlauben):
  ```bash
  sudo ufw allow in on lo to any port 8188
  sudo ufw allow in on tailscale0 to any port 8188
  sudo ufw deny 8188
  ```
- [x] **Ollama Härtung:** `OLLAMA_MAX_LOADED_MODELS=1` und `OLLAMA_KEEP_ALIVE=15m` in `/etc/systemd/system/ollama.service` eintragen.
- [ ] **ComfyUI Plugins:** `ComfyUI-Impact-Pack` (Face Detailer) und `4x-UltraSharp` (Upscaler) über den Manager installieren.
- [ ] **Zukunfts-Projekt:** Docker Desktop durch native Docker Engine (`docker-ce`) ersetzen, um den Linux-VM-Overhead vollständig zu beseitigen.

---

## 8. Spickzettel: Wichtige Terminal-Befehle

| Zweck | Befehl |
| :--- | :--- |
| **ComfyUI Status prüfen** | `systemctl --user status comfyui` |
| **ComfyUI Logs live mitlesen** | `journalctl --user -u comfyui -f` |
| **ComfyUI neu starten** | `systemctl --user restart comfyui` |
| **VRAM-Auslastung prüfen** | `rocm-smi --showmeminfo vram` |
| **Ollama VRAM leeren** | `systemctl restart ollama` |
| **Freien Festplattenspeicher prüfen** | `df -h /home` |
| **Checkpoints auflisten** | `ls -lh /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints/` |
| **Diffusionsmodelle auflisten** | `ls -lh /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/diffusion_models/` |
| **Fertige Workflows auflisten** | `ls -lh /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/user/default/workflows/` |
| **VRAM sofort komplett leeren (1-Klick)** | `/home/clemi/Projekte/LLM/image-video-setup/free_vram.sh` |
| **AMD GPU 60s-Watchdog Patch** | `sudo /home/clemi/Projekte/LLM/image-video-setup/apply_amd_gpu_fixes.sh` |
| **MiniMax-H3 Download starten** | `/home/clemi/Projekte/LLM/image-video-setup/download_minimax_h3.sh` |
| **Wan 2.1 Download starten** | `/home/clemi/Projekte/LLM/image-video-setup/download_wan.sh` |

---

## 9. Praxis-Architektur: Reines VRAM-Computing, Swap-Falle & MiniMax-H3 Tuning

### 9.1 Reines VRAM-Computing vs. RAM-Offloading
* **VRAM-Bandbreite (AMD Radeon PRO W7800):** **864 GB/s**.
* **PCIe 4.0 Schnittstelle:** max. **31 GB/s**.
* **Festplatten-Swap (NVMe):** nur **1–3 GB/s**.

Wann immer ein Modell vollständig in den VRAM passt, läuft die Berechnung ohne Latenzverzögerung mit voller GPU-Bandbreite.

### 9.2 Warum MiniMax H3 die 48 GB Grenze sprengt
* **Qwen3-VL 32B (Text- & Bild-Encoder):** 25,9 GB VRAM
* **MiniMax FL2VA DiT (Video-Kern):** 20,0 GB VRAM
* **Working Memory (Attention-Cache & Latents):** ca. 8,0 GB VRAM
* **Gesamtbedarf bei simultaner Vorhaltung:** **56,6 GB VRAM** (übersteigt 48 GB physischen VRAM).
* **Lösung:** Sequentieller Betrieb (Text analysieren ➔ Text-Encoder verwerfen ➔ Videokern laden).

### 9.3 Die Swap-Falle & Lösung
* **Problem:** Beim Modelltausch sicherte ComfyUI 26 GB inaktive Gewichte in den Host-RAM (`--cache-ram 8 32`). Der 64 GB RAM lief voll und Linux lagerte 20 GB auf den NVMe-Swap aus ➔ Desktop stockte / fror für 5 Minuten ein.
* **Lösung:** In `start_comfyui.sh` wurde `--cache-ram 4 16` hinterlegt. ComfyUI begrenzt den inaktiven Cache auf max. 16 GB. Der RAM bleibt unter 35 GB und Swap wird nicht ausgelöst.

### 9.4 Modell-Vergleich auf der 48 GB W7800

| Modell | Text-Encoder | Video-Core | Working Memory | Gesamt VRAM | Bleibt 100% im VRAM? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Wan 2.1 (14B)** | 6,3 GB (UMT5-XXL) | 27,2 GB | 6,0 GB | **~39,5 GB** | **Ja (Optimal für 48 GB)** |
| **Flux.1 [dev]** | 4,8 GB (T5-XXL) | 17,2 GB | 6,0 GB | **~28,0 GB** | **Ja (3–5 Sekunden)** |
| **MiniMax H3** | 25,9 GB (Qwen 32B) | 20,0 GB | 8,0 GB | **~56,6 GB** | ❌ Sequentieller Tausch |

### 9.5 MiniMax H3: Turbo-Modus vs. Standard-Modus
* `turbo_mode: false`: 50 Schritte, ca. 40 Sekunden pro Schritt = **~33 Minuten Rechenzeit** (0% bleibt für die ersten 2 Minuten stehen).
* `turbo_mode: true`: 8 Schritte, ca. 25 Sekunden pro Schritt = **~2,5 Minuten Gesamtrechenzeit** (Balken springt direkt auf 12% ➔ 25%...).

### 9.6 Wan 2.2 & Qwen-Image-2.1: Warum sie auf 48 GB optimal laufen
* **Wan 2.2 (Dual DiT 14B):**
  * Verwendet zwei spezialisierte DiTs: High-Noise (13,3 GB) und Low-Noise (13,3 GB) sowie UMT5-XXL (6,3 GB).
  * Da beide Diffusionskerne zusammen nur ~26,6 GB wiegen, passen Text-Encoder, High-Noise DiT, Low-Noise DiT und VAE **gleichzeitig zu 100 % in die 48 GB VRAM**.
  * Während 24 GB Grafikkarten (RTX 4090) mitten im Video-Sampling Modelle über PCIe tauschen müssen, arbeitet die W7800 unterbrechungsfrei in voller GPU-Bandbreite.
* **Qwen-Image-2.1 (SOTA Bild & Typografie):**
  * Nutzt den kompakten INT8-ConvRot-Kern (6,8 GB) + Qwen3.5 PE (8,9 GB).
  * Belegt nur ~18 GB VRAM und erzeugt fehlerfreien Text und native 2K-Bilder direkt im VRAM.

### 9.7 VRAM-Cleanup: Wann unnötig und wann notwendig?
* **Bei kontinuierlicher Arbeit mit EINEM Modell (Wan, FLUX, SDXL, Qwen-Image): VRAM-Cleanup ist UNNÖTIG!**
  * **SDXL:** ~6–8 GB VRAM | **Qwen-Image-2.1:** ~18–22 GB | **FLUX.1 [dev]:** ~20–24 GB | **Wan 2.1 / Wan 2.2:** ~24–38 GB.
  * Alle diese Modelle passen zu **100 % dauerhaft in die 48 GB VRAM** deiner AMD Radeon PRO W7800.
  * **Wichtig:** Keinen `VRAM-Cleanup`-Knoten im Workflow verwenden! Wenn die Modelle im VRAM verbleiben, starten Folge-Generierungen in **0 Sekunden** ohne Ladezeit. Ein Cleanup erzwingt bei jedem Run 15–45 Sekunden unnötiges Neuladen von der NVMe-SSD.
* **Wann VRAM-Cleanup sinnvoll und notwendig ist:**
  1. **Nur bei Modell-Wechsel:** z. B. von Wan ➔ MiniMax H3 oder von Flux ➔ Wan (einmalig im WebUI oben rechts auf `Unload Models` klicken, um alten Speicher sauber freizugeben).
  2. **Bei MiniMax H3 (als einzigem Modell über 48 GB):**
     * **Nach Bildladen / Konditionierung:** Der 26 GB Text- & Bild-Encoder (`qwen3vl_32b`) muss weichen, um Platz für den 20 GB DiT-Kern zu machen (regelt ComfyUI intern).
     * **Nach Generierung:** MiniMax über `Unload Models` entladen, damit der 26 GB Encoder nicht dauerhaft den Host-RAM blockiert.

---

## 10. Leitfaden: Der Turbo-Modus (Bedeutung, Qualität & Konfiguration)

### 10.1 Technische Funktionsweise (Wissensdestillation)
* **Standard-Diffusion:** Rechnet 20 bis 50 kleine Schritte aus dem Rauschen.
* **Turbo-Destillation (Lightning / Hyper):** Ein LoRA trainiert das Modell darauf, mehrere Rechenschritte in einen einzigen großen Schritt zusammenzufassen.
* **Ergebnis:** Reduktion von 50 auf 8 Schritte (MiniMax) bzw. von 20 auf 4 Schritte (Wan 2.2). Beschleunigung um Faktor 5 bis 13.

### 10.2 Einfluss auf die Qualität
* **Bewegung, Kamera & Dynamik:** 98 % identisch mit Standardmodellen.
* **Mikro-Details:** Ca. 5 % weicher bei Standbildern. In 24 FPS Bewegung für das menschliche Auge nicht wahrnehmbar.
* **Geschwindigkeit:** Wan 2.2 Videos rendern in ~60–90 Sekunden statt 6–8 Minuten; MiniMax H3 in 2,5 Minuten statt 33 Minuten.

### 10.3 Die goldenen Konfigurationsregeln
1. **CFG MUSS auf 1.0 gesetzt werden:** Turbo-LoRAs übersteuern und verbrennen bei CFG > 1.5. Bei CFG 1.0 entfällt zudem der negative Berechnungsschritt (doppelte Geschwindigkeit).
2. **Schrittzahl exakt einhalten:** Ein 4-Step-LoRA verlangt exakt 4 Schritte; ein 8-Step-LoRA exakt 8 Schritte.

---

## 11. Spezial-Leitfäden & Weiterführende Dokumentation

Für detaillierte Schritt-für-Schritt-Anleitungen stehen separate Praxisleitfäden zur Verfügung:

1. 🎵 [**Anleitung: Audio & Ton in KI-Videos integrieren**](file:///home/clemi/Projekte/LLM/image-video-setup/anleitung_audio_in_videos.md):  
   Muxing direkt in ComfyUI über `LoadAudio` an `VHS_VideoCombine`, KI-Soundeffekte (Foley AI) und FFmpeg-Befehle.
2. 🎬 [**Anleitung: Längere KI-Videos erstellen (10s, 30s, 1m+)**](file:///home/clemi/Projekte/LLM/image-video-setup/anleitung_laengere_videos.md):  
   Der „Last-Frame Chaining“-Workflow (Frame 49 ➔ Startbild für Clip 2), filmische Storyboard-Montage und Frame-Interpolation.
3. 💾 [**Leitfaden: Modell- & VRAM-Entladung**](file:///home/clemi/Projekte/LLM/image-video-setup/modelle_direkt_entladen.md):  
   Warum VRAM-Cleanup bei Wan/Flux unnötig ist und warum nur MiniMax H3 und Modellwechsel Entladen erfordern.
4. ⚙️ [**ComfyUI Knoten- & Parameterreferenz**](file:///home/clemi/Projekte/LLM/image-video-setup/nodes.md):  
   Detaillierte Erläuterungen zu Dual-DiT-Splits, samplers, Parametern und Stabilitäts-Flags (`start_comfyui.sh`).
5. 🐭 [**Regie- & Produktionsleitfaden: 15s-Kurzfilm (MiniMax H3)**](file:///home/clemi/Projekte/LLM/image-video-setup/anleitung_kurzfilm_maus_minimax.md):  
   Vollständiges Storyboard, Kamera- & Szenen-Settings, Audio-Prompts und FFmpeg-Concat für „Die kleine Maus im Käseladen“.
6. ⛓️ [**Praxisleitfaden: Multi-Stage Workflows & Video-Erweiterung**](file:///home/clemi/Projekte/LLM/image-video-setup/anleitung_multistage_und_video_erweiterung.md):  
   Automatisierte Verkettung in ComfyUI, Abspeichern aller Einzelclips plus Gesamtfilm und nachträgliches Erweitern ohne Neurendern.
7. 📊 [**Stabilitäts- & Auflösungsmatrix (MiniMax H3 vs. Wan 2.2)**](file:///home/clemi/Projekte/LLM/image-video-setup/SPEICHER_UND_AUFLOESUNG_MATRIX.md):  
   Warum Megapixel quadratisch skalieren, warum 0.8 mit MiniMax H3 crasht und wie man das System mit 0.4 dauerhaft lag-frei hält.

