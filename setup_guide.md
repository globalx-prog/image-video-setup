# Bild- & Video-KI Setup (48GB VRAM AMD Edition)

Dieses Setup verbindet deine **AMD Radeon PRO W7800 48GB** nativ mit **ComfyUI (ROCm)** und integriert die Bildgenerierung direkt in **Open WebUI**.

---

## 🏛 Architektur & Status

```
                 [ Browser / Client ]
                   │              │
                   ▼              ▼
           [ Open WebUI ]    [ ComfyUI Node-Editor ]
           (Port 3000)       (Port 8188 / Service)
                   │              │
                   │ (HTTP API)   │ (ROCm 6.4)
                   └──────►───────┴────────► [ AMD Radeon PRO W7800 48GB VRAM ]
```

* **ComfyUI Engine:** Läuft nativ als systemd-Dienst (`comfyui.service`), gekoppelt an Docker Desktop.
* **ROCm 6.4 & PyTorch 2.9:** Volle GPU-Beschleunigung ohne Virtualisierungs-Bottleneck.
* **Open WebUI:** Verknüpft via `COMFYUI_BASE_URL=http://100.102.224.36:8188/`.

---

## 📦 Installierte Modelle (Bild & Video)

* **FLUX.1 Dev FP8** (`flux1-dev-fp8.safetensors`, 17.2 GB) – **Bereit ✅**
  * Das unangefochtene Nr.-1-Open-Weights-Bildmodell weltweit. Maximale Detailfülle und Prompt-Treue (20–28 Steps).
* **FLUX.1 Schnell FP8** (`flux1-schnell-fp8.safetensors`, 17 GB) – **Bereit ✅**
  * Höchste Prompt-Treue & Fotorealismus, extrem schnell (4 Steps). Standard für Open WebUI.
* **SD 3.5 Large FP8** (`sd3.5_large_fp8_scaled.safetensors`, 14.9 GB) – **Bereit ✅**
  * Stability AI Flaggschiff (8B Parameter) mit exzellenter Typografie und flexibler Bildästhetik.
* **SDXL Base 1.0** (`sd_xl_base_1.0.safetensors`, 6.5 GB) – **Bereit ✅**
  * Bewährter Standard für vielfältige Stile und LoRA-Kombinationen.
* **LTX-Video 2B** (`ltx-video-2b-v0.9.1.safetensors`, 5.4 GB) – **Bereit ✅**
  * Schneller DiT für Text-to-Video & Image-to-Video.
* **SVD-XT** (`svd_xt.safetensors`, 9.0 GB) – **Bereit ✅**
  * Stable Video Diffusion XT für flüssige 25-Frame Image-to-Video Animationen.

### B. High-End Video: Wan 2.1 14B (Alibaba)
Da du **48 GB VRAM** hast, ist das **14B-Modell in voller BF16-Qualität** (nicht quantisiert) das absolute Optimum für dein System:
* **Diffusion Model:** `ComfyUI/models/diffusion_models/wan2.1_t2v_14B_bf16.safetensors` (~28.5 GB)
* **Text Encoder:** `ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` (~6.7 GB)
* **VAE:** `ComfyUI/models/vae/wan_2.1_vae.safetensors` (~254 MB)

---

## 🚀 Wie werden die Modelle genutzt?

### 1. In Open WebUI (Bequemer Chat-Modus für Bilder)
1. Öffne Open WebUI im Browser (`http://localhost:3000`).
2. Gehe auf **Admin-Panel ➔ Einstellungen ➔ Bilder**.
3. Überprüfe die Einstellungen:
   * **Engine:** `comfyui`
   * **ComfyUI Base URL:** `http://100.102.224.36:8188/`
   * **Modell / Checkpoint:** Wähle `flux1-schnell-fp8.safetensors` oder `sd_xl_base_1.0.safetensors`.
4. Klicke auf **Speichern**.
5. Im Chat kannst du nun per Klick auf das Bild-Icon oder via Text-Prompt direkt Bilder erzeugen lassen.

### 2. In ComfyUI (Pro-Modus für Bilder & Videos)
1. Öffne **`http://localhost:8188`**.
2. **Workflows nutzen:**
   * **Bilder (FLUX/SDXL):** Bild per Drag & Drop ins Browserfenster ziehen – der Workflow lädt sich automatisch.
   * **Videos (LTX-Video / SVD-XT):** Im Node `Load Checkpoint` das Modell wählen und über `Video Combine` (VideoHelperSuite) rendern.
   * **Videos (Wan 2.1 14B):** Nutze die Nodes `Load Diffusion Model` (wählt `wan2.1_t2v_14B_bf16`), `Load CLIP` (wählt `umt5_xxl_fp8`) und `Load VAE` (wählt `wan_2.1_vae`).

---

## 🛠 Verwaltung & Überwachung

* **Status prüfen:** `systemctl --user status comfyui`
* **Logs ansehen:** `journalctl --user -u comfyui -f`
* **Wan-Download verfolgen:**
  ```bash
  tail -f /home/clemi/.gemini/antigravity/brain/95954951-a12e-4876-9e38-bf7f2c6f9b59/.system_generated/tasks/task-309.log
  ```
* **Dateien prüfen:**
  ```bash
  ls -lh /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints/
  ls -lh /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/diffusion_models/
  ```
