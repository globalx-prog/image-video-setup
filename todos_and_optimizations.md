# 📋 TODOs & Funktionsoptimierungen (LLM, Bild- & Video-Stack)

Dieses Dokument erfasst alle offenen Aufgaben, empfohlene Funktionserweiterungen und Performance-Härtungen für deine lokale KI-Infrastruktur auf der **AMD Radeon PRO W7800 (48 GB VRAM)**.

---

## 🚀 1. Offene Aufgaben (Sofort & Kurzfristig)

- [ ] **Open WebUI Bild-Konfiguration finalisieren:**
  - In Open WebUI (`http://localhost:3000`) unter *Admin ➔ Einstellungen ➔ Bilder* als Checkpoint `flux1-schnell-fp8.safetensors` auswählen und speichern.
  - Test-Prompt im Chat absetzen (z. B. *"Ein fotorealistischer Astronaut auf dem Mars"*), um den Fluss Chat ➔ ComfyUI ➔ ROCm zu verifizieren.
- [ ] **Erstes Wan 2.1 Video in ComfyUI testen:**
  - `http://localhost:8188` öffnen.
  - Wan 2.1 Workflow laden (Verbindung von `wan2.1_t2v_14B_bf16` mit `umt5_xxl_fp8` und `wan_2.1_vae`).
  - Einen kurzen 3-Sekunden-Clip berechnen und Renderzeit/VRAM-Füllstand per `rocm-smi` prüfen.
- [ ] **Firewall-Härtung für ComfyUI Port 8188:**
  - ComfyUI lauscht unauthentifiziert auf `0.0.0.0:8188`. Für Absicherung gegen andere Geräte im lokalen WLAN:
    ```bash
    sudo ufw allow in on lo to any port 8188
    sudo ufw allow in on tailscale0 to any port 8188
    sudo ufw deny 8188
    ```

---

## ⚡ 2. VRAM- & Stabilitäts-Optimierungen

- [ ] **Ollama VRAM-Kollisionsschutz aktivieren:**
  - Verhindern, dass Ollama stundenlang VRAM blockiert, während ComfyUI schwere 14B-Videomodelle laden will.
  - In `/etc/systemd/system/ollama.service` folgende Parameter unter `[Service]` ergänzen:
    ```ini
    Environment="OLLAMA_MAX_LOADED_MODELS=1"
    Environment="OLLAMA_KEEP_ALIVE=15m"
    ```
  - Aktivieren via:
    ```bash
    sudo systemctl daemon-reload && sudo systemctl restart ollama
    ```
- [ ] **Automatischer VRAM-Wächter (Optional / Script):**
  - Ein kleines Helper-Skript bereitstellen, das vor dem Start großer Renderjobs in ComfyUI prüft, ob Ollama VRAM belegt, und dieses bei Bedarf temporär entlädt (`ollama stop ...`).

---

## 🛠 3. Infrastruktur- & System-Modernisierung

- [ ] **Ablösung von Docker Desktop durch native Docker Engine (`docker-ce`):**
  - *Hintergrund:* Docker Desktop läuft auf Linux in einer virtuellen Maschine und isoliert die AMD-Hardware (`/dev/kfd`).
  - *Ziel:* Docker Desktop deinstallieren und stattdessen die offizielle, native Ubuntu Docker Engine (`docker-ce`, `docker-compose-plugin`) installieren.
  - *Vorteil:* Volle Bare-Metal-Performance für alle Container, direkte GPU-Durchreichung für Docker-Container möglich, geringerer RAM- und CPU-Overhead.
  - *Aufwand:* Gering, da alle `docker-compose.yml` Dateien 1:1 unverändert weitergenutzt werden können.
- [ ] **Bereinigung alter Docker-Volumes & Snapshots:**
  - Temporäre Cache-Dateien und veraltete Test-Images prüfen und säubern (`docker system prune -f`), um permanent über 100 GB freien Speicher zu sichern.

---

## 🎨 4. Bild- & Video-Funktionserweiterungen

- [ ] **Upscaler-Modelle für ComfyUI hinzufügen (4K-Skalierung):**
  - Für hochauflösendes Nachschärfen von FLUX-Bildern und Videoclips:
  - Über *Manager ➔ Install Models* beliebte Upscaler installieren:
    - `4x-UltraSharp`
    - `4x_NMKD_Superscale-SP_178000_G`
    - `RealESRGAN_x4plus`
- [ ] **Face-Restoration / Face-Swapping (ReActor Node):**
  - Über *Manager ➔ Install Custom Nodes* das Plugin `comfyui-reactor-node` installieren (erlaubt präzises Face-Swapping und Gesichtsreparatur in generierten Bildern/Videos).
- [ ] **ComfyUI-Impact-Pack installieren:**
  - Das wichtigste Standard-Plugin für automatisiertes Inpainting, Gesichtsnachschärfen (*Face Detailer*) und Kantenoptimierung.
- [ ] **FLUX LoRAs einrichten:**
  - Einen Unterordner für spezialisierte LoRA-Stile anlegen und über Civitai beliebte LoRAs für FLUX.1 testen (z. B. Realism LoRAs, spezifische Kunststile oder Charakterkonsistenz).

---

## 🌐 5. Remote-Zugriff & Schnittstellen

- [ ] **ComfyUI über Cloudflare Tunnel (Remote-Zugriff von unterwegs):**
  - Aktuell ist ComfyUI nur lokal oder über Tailscale erreichbar.
  - Falls gewünscht: Im Cloudflare Zero Trust Dashboard einen Public Hostname einrichten (z. B. `comfy.nas-clemens.de` ➔ `http://localhost:8188`) und **zwingend mit Cloudflare Access (E-Mail OTP / PIN) schützen**, da ComfyUI kein eigenes Login besitzt.
- [ ] **Mobile Nutzung über Tailscale:**
  - Auf Smartphone/Tablet Tailscale aktivieren und `http://100.102.224.36:8188` aufrufen, um von überall unterwegs Workflows zu steuern und Renderaufträge zu starten.

---

## 📊 Status-Übersicht des Stacks

| Komponente | Version / Typ | Hardware-Status | Offene Optimierung |
| :--- | :--- | :--- | :--- |
| **Ollama** | 0.34.4 (Host) | AMD ROCm gfx1100 (45 GB erkannt) | `MAX_LOADED_MODELS=1` & `KEEP_ALIVE=15m` |
| **Open WebUI** | v0.11.4 (Docker) | Angebunden via Tailscale-IP | Checkpoint in GUI als Standard setzen |
| **ComfyUI** | 0.38.0 (Native uv) | PyTorch 2.9.1+rocm6.4 (48 GB VRAM) | Impact Pack / Upscaler installieren |
| **Wan 2.1 14B** | BF16 (Native) | 35.4 GB geladen (Diffusion, Text, VAE) | Ersten Testrender ausführen |
| **Sicherheit** | Cloudflare Tunnel | `openwebui.nas-clemens.de` geschützt | UFW-Portabsicherung für 8188 |

