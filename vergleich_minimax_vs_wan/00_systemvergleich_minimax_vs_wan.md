# 🥊 Systemvergleich: MiniMax H3 vs. WAN 2.2 auf AMD Radeon PRO W7800 (48 GB VRAM)
## Technologie-Gegenüberstellung, Renderzeiten, Audio-Aufwand & Empfehlungen

> **Hardware:** AMD Radeon PRO W7800 (48 GB VRAM) | 64 GB RAM | Ubuntu Linux | ROCm 6.4

---

## 📊 Der große Direktvergleich auf einen Blick

| Kriterium | 🏆 MiniMax H3 (Omni Video+Audio) | 🥈 WAN 2.2 (14B FP8 Scaled) |
| :--- | :--- | :--- |
| **Modell-Architektur** | Joint Audio-Video DiT (14B) + Qwen3-VL 32B | Reines Video-DiT (14B) + UMT5-XXL |
| **VRAM-Fußabdruck** | ca. **38 – 42 GB** (UNET 20GB + Qwen3-VL 25GB) | ca. **18 – 22 GB** (FP8 DiT 13GB + UMT5 6GB) |
| **Tonspur (Audio)** | **100 % Nativ synchron** (32-Kanal Audio-VAE) | **Kein nativer Ton** (stumm) |
| **Renderzeit (5s Clip)** | ca. **70 – 85 Sekunden** (4-8 Steps Turbo) | ca. **30 – 45 Sekunden** (4 Steps Lightx2v) |
| **Renderzeit (5 Min Film)** | ca. **75 – 85 Minuten** (ohne Modell-Entladen) | ca. **35 – 45 Minuten** (ohne Modell-Entladen) |
| **Physik & Dynamik** | Sehr gut bei Gesichtern, Mimik und Sprechen | **Überragend** bei Flüssigkeiten, Stoff & Physik |
| **Charakter-Konsistenz** | Hervorragend über **Ref2V (`<Picture 1>`)** | Sehr gut über **I2V + First-Frame-Handoff** |
| **Dauerhaft im VRAM** | **Ja** (bei 48 GB VRAM mit `offload_model: false`) | **Ja** (sehr viel VRAM-Puffer frei für 4K) |

---

## 🔊 Wie aufwändig ist das nachträgliche Generieren / Hinzufügen der Tonspur bei WAN?

Da WAN 2.2 stumm rendert, muss der Ton extern hinzukommen. Hier sind die **4 Methoden geordnet nach Aufwand**:

### Methode 1: Vollautomatisch per Skript (Aufwand: 0 Minuten!)
* **Wie es funktioniert:** Unser Automatisierungsskript (`wan_movie_maker.py`) liest das Drehbuch. Wenn dort z. B. steht `audio: "rain, footsteps, jazz music"`, nimmt das Skript automatisch eine passende Hintergrund-Audiodatei aus einem Sound-Ordner (oder mixt sie) und verbindet Bild und Ton per FFmpeg:
  ```bash
  ffmpeg -y -i clip_stumm.mp4 -i audio.mp3 -c:v copy -c:a aac -shortest clip_mit_ton.mp4
  ```
* **Zeitaufwand:** **0,2 Sekunden** pro Clip (reines Kopieren, kein Rendern).
* **Fazit:** Für automatisierte Langfilme absolut schmerzfrei.

---

### Methode 2: Direkt in ComfyUI beim Rendern (Aufwand: 1 Klick)
* **Wie es funktioniert:** Im ComfyUI-Workflow wird der Knoten **`LoadAudio`** (oder `LoadAudioUpload`) mit dem Audio-Eingang von **`VHS_VideoCombine`** verbunden.
* **Ergebnis:** ComfyUI schneidet den geladenen Sound automatisch auf die exakte Videolänge zu und spuckt direkt ein fertiges MP4 mit Ton aus.

---

### Methode 3: KI-generierter Sound (Video-to-Audio Foley AI)
* **Wie es funktioniert:** Ein spezielles Audio-KI-Modell wie **`MMAudio`** oder **`AudioLDM2`** analysiert die Video-Frames von WAN 2.2 und generiert automatisch synchrone Soundeffekte (Schritte, Wind, Türknallen, Motoren).
* **Aufwand:** Erfordert das Laden eines zweiten Modells (ca. 4 GB VRAM) und ca. 10–15 Sekunden Rechenzeit pro Clip.

---

### Methode 4: Professioneller Schnitt (DaVinci Resolve / CapCut)
* **Wie es funktioniert:** Du exportierst alle WAN 2.2 Szenen als MP4, importierst sie in DaVinci Resolve (kostenlos unter Linux) oder CapCut und legst 3 Audiospuren an:
  1. *Spur 1: Atmosphäre (Ambience)* – Regen, Wind, Stadt.
  2. *Spur 2: Soundeffekte (Foley)* – Schritte, Türklinke, Geschirr.
  3. *Spur 3: Musik (Score)* – Emotionale Begleitmusik.
* **Aufwand:** 15–30 Minuten manuelle Schnittarbeit für einen 5-Minuten-Film.
* **Ergebnis:** Das Ergebnis klingt wie ein echter Hollywood-Film (deutlich besser als die interne KI-Audio-VAE von MiniMax H3!).

---

## 💡 Wann lohnt sich MiniMax H3 und wann WAN 2.2?

### Nimm MiniMax H3, wenn:
1. **Du 100 % Automatisierung willst:** Drehbuch rein $\rightarrow$ fertiger Film mit passenden Geräuschen und Ton raus, ohne einen Finger zu rühren.
2. **Charaktere sprechen oder Geräusche machen:** MiniMax H3 synchronisiert Lippen und Handlungen direkt mit den Audio-Wellenformen.
3. **Du ein „All-in-One“-Paket bevorzugst.**

### Nimm WAN 2.2, wenn:
1. **Geschwindigkeit priorisiert ist:** Mit dem 4-Step Lightx2v LoRA rendert WAN 2.2 in **unter 40 Sekunden pro 5s-Clip** (doppelt so schnell wie H3!).
2. **Du komplexe Physik simulieren willst:** Wasser, Explosionen, wehende Haare, dynamische Kameraflüge.
3. **Du den Ton ohnehin professionell in DaVinci Resolve oder CapCut vertonen willst.**

