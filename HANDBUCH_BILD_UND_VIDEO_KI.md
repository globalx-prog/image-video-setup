# 🎨 Das Kompletthandbuch: Lokales Bild- & Video-KI Setup
> **Hardware:** AMD Radeon PRO W7800 (48 GB VRAM) | 64 GB RAM | Linux Ubuntu  
> **Architektur:** Nativ ComfyUI (ROCm 6.4 / PyTorch 2.9) + Docker Open WebUI (via Tailscale)  
> **Stand:** Oktober 2026

---

## 📑 Inhaltsverzeichnis
1. [Architektur & System-Überblick](#1-architektur--system-überblick)
2. [Installierte Modelle & Empfohlene Einsatzbereiche](#2-installierte-modelle--empfohlene-einsatzbereiche)
3. [Tägliche Nutzung: Schritt für Schritt](#3-tägliche-nutzung-schritt-für-schritt)
   - [A. Schnelle Bilder im Chat (Open WebUI)](#a-schnelle-bilder-im-chat-open-webui)
   - [B. Videos & High-End Grafik (ComfyUI)](#b-videos--high-end-grafik-comfyui)
   - [C. ComfyUI ohne Frust verstehen ("Drag & Drop"-Magie)](#c-comfyui-ohne-frust-verstehen-drag--drop-magie)
4. [Fehlerbehebung & Praxiserkenntnisse (z. B. Error 400)](#4-fehlerbehebung--praxiserkenntnisse-z-b-error-400)
5. [Modelle finden, testen & neue Funktionen nachrüsten](#5-modelle-finden-testen--neue-funktionen-nachrüsten)
6. [VRAM-Sicherheit & Stabilitätsschutz (Freeze-Prävention)](#6-vram-sicherheit--stabilitätsschutz-freeze-prävention)
7. [Roadmap: Offene TODOs & Optimierungen](#7-roadmap-offene-todos--optimierungen)
8. [Spickzettel: Wichtige Terminal-Befehle](#8-spickzettel-wichtige-terminal-befehle)

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
  * *Eigenschaft:* Höchste physikalische Bewegungskonsistenz und Detailtiefe. Nutzt deine 48 GB VRAM voll aus.
* **MiniMax-H3 (Hailuo 03) – Video- & Native Audio-Generierung (AMD ROCm / HIP Edition):**
  * **Diffusion Core:** `models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` (19.5 GB)
  * **Text Encoder (AMD-nativ):** `models/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (25.3 GB)
  * **Video VAE:** `models/vae/minimax_h3_video_vae_int8_convrot.safetensors` (2.6 GB)
  * **Audio VAE:** `models/vae/minimax_h3_audio_vae_fp32.safetensors` (580 MB)
  * **Turbo LoRA (8-Steps):** `models/loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (1.8 GB)
  * *Wichtige AMD-Besonderheit:* Standard-Workflows verlinken oft auf NVIDIA-`nvfp4`. Auf AMD ROCm muss zwingend die `int8_convrot`-Variante gewählt werden (per Symlink und Workflow-Preset automatisch abgesichert).

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
3. **Videos mit Wan 2.1 (14B):**
   * ComfyUI unterstützt Wan 2.1 nativ über `Load Diffusion Model` (`wan2.1_t2v_14B_bf16`), `Load CLIP` (`umt5_xxl_fp8`) und `Load VAE` (`wan_2.1_vae`).
   * Die Ausgabe wird an den Node **`Video Combine`** (aus der installierten *VideoHelperSuite*) geleitet, der direkt ein `.mp4`-Video auf die Platte schreibt.
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

## 4. Fehlerbehebung & Praxiserkenntnisse (z. B. Error 400)

### Der "Error 400 (Bad Request)" in Open WebUI
* **Symptom:** Open WebUI meldet beim Generieren: `Serverfehler (400): Error while queuing prompt`.
* **Ursache:** In den ComfyUI-Logs (`journalctl --user -u comfyui`) stand:
  `Value not in list: ckpt_name: 'model.safetensors' not in [...]`  
  Open WebUI hat den Standard-Platzhalternamen `model.safetensors` angefragt, der nicht existierte.
* **Lösung:**
  1. Auf Dateisystemebene wurde ein Symlink `model.safetensors -> flux1-schnell-fp8.safetensors` eingerichtet.
  2. In Open WebUI unter *Admin ➔ Einstellungen ➔ Bilder* muss explizit der tatsächliche Dateiname (z. B. `flux1-schnell-fp8.safetensors` oder `flux1-dev-fp8.safetensors`) eingetragen und gespeichert werden.

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

Dein Rechner besitzt **48 GB VRAM**, **64 GB System-RAM** und **36 GB Swap**. Dennoch ist Vorsicht geboten, wenn Sprachmodelle und Videomodelle gleichzeitig laufen:

1. **Kein automatisches Entladen bei 24h Keep-Alive:**  
   In `ollama.service` ist aktuell `OLLAMA_KEEP_ALIVE=24h` konfiguriert. Ein einmal geladenes großes LLM (z. B. 70B mit ~38 GB VRAM) bleibt dauerhaft im Speicher.
2. **Kollision mit ComfyUI:**  
   Wenn Ollama 38 GB belegt und du in ComfyUI das 28.5 GB schwere Wan 2.1 startest, kann ROCm den Speicher nicht allokieren. Es folgt ein `OutOfMemoryError`.
3. **Die Lösung:**
   * Vor großen Video-Renderings in ComfyUI den VRAM kurz freiräumen:
     ```bash
     systemctl restart ollama
     ```
   * Dauerhafte Absicherung in `/etc/systemd/system/ollama.service`:
     ```ini
     Environment="OLLAMA_MAX_LOADED_MODELS=1"
     Environment="OLLAMA_KEEP_ALIVE=15m"
     ```

---

## 7. Roadmap: Offene TODOs & Optimierungen

- [x] ComfyUI ROCm Nativ-Setup mit PyTorch 2.9 & AMD GPU-Erkennung
- [x] Open WebUI Anbindung via Tailscale-IP & Docker Compose
- [x] FLUX.1 Schnell & FLUX.1 Dev einrichten
- [x] SD 3.5 Large & SDXL Base einrichten
- [x] LTX-Video 2B & SVD-XT einrichten
- [x] Wan 2.1 14B (BF16 Diffusion + Text Encoder + VAE) bereitstellen
- [x] Fehler 400 Fallback-Symlink (`model.safetensors`) anlegen
- [ ] **Open WebUI:** Im Admin-Panel `flux1-schnell-fp8.safetensors` oder `flux1-dev-fp8.safetensors` final als Modell speichern und Test-Generierung prüfen.
- [ ] **Firewall:** Port 8188 mit UFW absichern (nur Localhost & Tailscale erlauben):
  ```bash
  sudo ufw allow in on lo to any port 8188
  sudo ufw allow in on tailscale0 to any port 8188
  sudo ufw deny 8188
  ```
- [ ] **Ollama Härtung:** `OLLAMA_MAX_LOADED_MODELS=1` und `OLLAMA_KEEP_ALIVE=15m` in `/etc/systemd/system/ollama.service` eintragen.
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
| **Modelle auflisten** | `ls -lh /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints/` |

