# 🎨 Tägliche Nutzungsanleitung & Dokumentation: Bild- & Video-KI

Dieses Handbuch ist dein kompakter Leitfaden für den täglichen Einsatz deiner Bild- und Video-Generatoren auf deiner **AMD Radeon PRO W7800 (48 GB VRAM)**.

---

## ⚡ Schnellstart: Der tägliche Workflow

Dein System ist so konfiguriert, dass **ComfyUI automatisch im Hintergrund startet**, sobald Docker Desktop aktiv ist (`comfyui.service`).

### Welches Tool nehme ich wofür?

| Ziel | Empfohlenes Tool | Zugriff | Warum? |
| :--- | :--- | :--- | :--- |
| **Schnelle Bilder / Chat** | **Open WebUI** | `http://localhost:3000` (oder `https://openwebui.nas-clemens.de`) | Schnell, unkompliziert, direkt im Gesprächsverlauf. |
| **Videos (T2V & I2V)** | **ComfyUI** | `http://localhost:8188` | Volle Kontrolle, Video-Player, MP4-Export. |
| **High-End Bilder / LoRAs / Upscaling** | **ComfyUI** | `http://localhost:8188` | Feintuning, hochauflösende Skalierung (4K), Face-Fixing. |

---

## 🖼 1. Bilder generieren über Open WebUI (Bequemer Modus)

1. Öffne Open WebUI im Browser.
2. Stelle sicher, dass unter **Admin ➔ Einstellungen ➔ Bilder** folgendes gewählt ist:
   * **Engine:** `comfyui`
   * **URL:** `http://100.102.224.36:8188/`
   * **Modell:** `flux1-schnell-fp8.safetensors` (Empfehlung für Speed & Qualität) oder `sd_xl_base_1.0.safetensors`.
3. **Im Chat:**
   * Klicke auf das **Bild-Icon** im Eingabefeld oder tippe deinen Prompt ein.
   * Das Bild wird innerhalb weniger Sekunden via ComfyUI auf deiner AMD-Karte berechnet und direkt im Chat angezeigt.

---

## 🎬 2. Bilder & Videos generieren über ComfyUI (Pro-Modus)

Öffne **`http://localhost:8188`**.

### Der beste Trick: "Drag & Drop" statt Nodes selbst bauen!
Du musst in ComfyUI selten Kabel selbst verbinden:
1. Lade dir ein Bild oder Video von Plattformen wie [Civitai](https://civitai.com) oder [OpenArt](https://openart.ai) herunter.
2. Ziehe die Datei per **Drag & Drop** direkt in dein ComfyUI-Browserfenster.
3. ComfyUI liest die eingebetteten Metadaten und baut den **kompletten Node-Workflow automatisch nach**!
4. Passe nur noch den Prompt-Text an und klicke rechts auf **"Queue Prompt"**.

### Deine installierten Modelle & empfohlene Einsatzbereiche:

* **Bilder:**
  * `flux1-dev-fp8.safetensors` *(Checkpoint)*: **Das weltbeste Open-Source-Bildmodell (Platz 1)**. Maximale Detailtreue, Hauttextur & Prompt-Genauigkeit (ideal für High-End-Renderings mit 20–28 Steps).
  * `flux1-schnell-fp8.safetensors` *(Checkpoint)*: Extrem schnell (4 Steps), fotorealistisch, kann lesbaren Text in Bildern darstellen. Perfekt für Open WebUI Chat.
  * `sd3.5_large_fp8_scaled.safetensors` *(Checkpoint)*: **Stability AI Flaggschiff (8B Parameter)**. Exzellente Typografie, flexibler Stil und starke Bildkomposition.
  * `sd_xl_base_1.0.safetensors` *(Checkpoint)*: Größte Community-Unterstützung für spezielle Stile und LoRAs.
* **Videos:**
  * `wan2.1_t2v_14B_bf16.safetensors` *(Diffusion Model)*: **Dein Flaggschiff-Videomodell**. Unglaubliche physikalische Bewegungskonsistenz und Detailtiefe. Nutzt deine 48 GB VRAM voll aus.
  * `ltx-video-2b-v0.9.1.safetensors` *(Checkpoint)*: Blitzschnelle 24fps Text-to-Video & Image-to-Video Clips.
  * `svd_xt.safetensors` *(Checkpoint)*: Verwandelt ein Standbild (Image-to-Video) in eine flüssige 25-Frame Kamerafahrt.

---

## 🔍 3. Wie teste ich andere Modelle & wo finde ich neue Funktionen?

### A. Der ComfyUI-Manager (Der interne "App Store")
In ComfyUI findest du rechts unten im Steuerungsmenü den Button **"Manager"**:
1. **"Install Models":**
   * Durchsuche einen riesigen Katalog nach neuen Checkpoints, LoRAs, Upscalern und ControlNets.
   * Ein Klick auf *Install* lädt das Modell automatisch in den richtigen Ordner herunter.
2. **"Install Custom Nodes":**
   * Hier installierst du neue Funktionen (z. B. Face-Swapping mit *ReActor*, Detailer mit *Impact Pack*, oder neue Video-Engines).
3. **"Install Missing Custom Nodes":**
   * Wenn du einen fremden Workflow per Drag & Drop importierst und rote Kästchen siehst, klicke hierauf: Der Manager installiert alle fehlenden Nodes automatisch per 1-Klick!

### B. Die besten Quellen für neue Modelle & Workflows
* **[Civitai.com](https://civitai.com):** Die weltgrößte Plattform für SDXL-, FLUX- und Video-Modelle, LoRAs und fertige ComfyUI-Workflows.
* **[OpenArt.ai / Workflows](https://openart.ai/workflows):** Riesige Galerie von fertigen ComfyUI-Pipelines zum Herunterladen.
* **[Hugging Face](https://huggingface.co):** Die Quelle für neueste Open-Source-Forschungsmodelle (wie Wan, Mochi, Hunyuan, FLUX).

### C. Manuell heruntergeladene Modelle ablegen
Falls du `.safetensors`-Dateien manuell herunterlädst, speichere sie in diesen Ordnern:
* **Komplette Checkpoints (FLUX, SDXL, LTX-Video, SVD):**  
  `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints/`
* **Modulare Diffusion Models (z. B. Wan 2.1):**  
  `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/diffusion_models/`
* **LoRAs (Stile, Charaktere, Effekte):**  
  `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/loras/`
* **Upscaler (4K/8K KI-Skalierung):**  
  `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/upscale_models/`

*Tipp:* Nach dem Hinzufügen einer Datei in ComfyUI einfach rechts auf **"Refresh"** klicken.

---

## 🛡 4. VRAM-Management im Alltag (Kollisionen vermeiden)

Du hast **48 GB VRAM**, was extrem viel ist. Dennoch gilt als Faustregel:
* **Vor großen Video-Rendern (z. B. Wan 2.1 14B):**
  Wenn du zuvor stundenlang mit einem riesigen Sprachmodell (z. B. 70B in Ollama) gechattet hast, gib den VRAM kurz frei:
  ```bash
  systemctl restart ollama
  ```
* **Status des VRAMs prüfen:**
  ```bash
  rocm-smi --showmeminfo vram
  ```

---

## 🔧 5. Nützliche Terminal-Befehle

| Aktion | Befehl |
| :--- | :--- |
| **ComfyUI Status prüfen** | `systemctl --user status comfyui` |
| **ComfyUI Live-Logs ansehen** | `journalctl --user -u comfyui -f` |
| **ComfyUI neu starten** | `systemctl --user restart comfyui` |
| **VRAM-Auslastung prüfen** | `rocm-smi` |
| **Freien Festplattenspeicher prüfen** | `df -h /home` |

