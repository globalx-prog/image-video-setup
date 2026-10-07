# 🛡️ Sicherheitsguide: Gemeinsame Nutzung von Ollama & ComfyUI
> **Hardware:** AMD Radeon PRO W7800 (48 GB VRAM) | 64 GB RAM | Ubuntu Linux (ROCm 6.4)  
> **Ziel:** 100% Stabilität – Nie wieder System-Freezes bei gleichzeitiger Text-, Bild- und Videogenerierung.

---

## 📑 Inhaltsverzeichnis
1. [Forensische Ursachen-Analyse des gestrigen Absturzes](#1-forensische-ursachen-analyse-des-gestrigen-absturzes)
2. [Das Kernproblem: Zwei unabhängige KI-Engines auf einer GPU](#2-das-kernproblem-zwei-unabhängige-ki-engines-auf-einer-gpu)
3. [Die VRAM-Budget-Matrix (Was darf gleichzeitig laufen?)](#3-die-vram-budget-matrix-was-darf-gleichzeitig-laufen)
4. [Die 3 Betriebsmodi für den Alltag](#4-die-3-betriebsmodi-für-den-alltag)
5. [Die 4-stufige Schutzarchitektur (Bereits eingerichtet)](#5-die-4-stufige-schutzarchitektur-bereits-eingerichtet)
6. [Praxis-Spickzettel & Notfall-Befehle](#6-praxis-spickzettel--notfall-befehle)

---

## 1. Forensische Ursachen-Analyse des gestrigen Absturzes

Die System- und Kernel-Logs von gestern Abend (**22:14 bis 22:17 Uhr**) belegen den exakten Hergang des Absturzes:

```text
[22:14:06] ComfyUI: Requested to load WanTEModel (6.4 GB VRAM)
[22:14:38] ComfyUI: Requested to load WAN21 14B (26.2 GB VRAM)
[22:14:15] kernel: workqueue: svm_range_restore_work [amdgpu] hogged CPU for >10000us 2051 times
[22:17:13] kernel: amdgpu 0000:03:00.0: Fence fallback timer expired on ring sdma0
[22:17:19] kernel: amdgpu: ring sdma0 timeout ... device wedged, but recovered through reset
[22:17:34] kernel: amdgpu: ring comp_1.2.1 timeout ... Process Xwayland ... device wedged
--> [HARD FREEZE: Desktop reagiert nicht mehr, Monitor friert ein, Hard Reboot erforderlich]
```

### Was ist hier physikalisch passiert?
1. **Ollama war noch aktiv geladen:**  
   Aus einem vorherigen Chat hielt Ollama ein großes Sprachmodell inklusive KV-Cache und Prompt-Cache im VRAM (**ca. 22–24 GB VRAM belegt**).
2. **ComfyUI startete parallel:**  
   ComfyUI forderte für Wan 2.1 (14B) und Text-Encoder **weitere 32,6 GB VRAM** an.
3. **Der Speicherüberlauf:**  
   `24 GB (Ollama) + 32,6 GB (Wan) + 2 GB (Desktop/Wayland) = ~58,6 GB Gesamtforderung!`  
   Die Grafikkarte besitzt jedoch **nur 48 GB physischen VRAM**.
4. **Der fatale PCIe-Stau (SDMA-Engine Timeout):**  
   ROCm und der Linux-Treiber `amdgpu` versuchten verzweifelt, den VRAM-Überlauf über PCIe in den Arbeitsspeicher auszulagern (*Shared Virtual Memory / SVM Page Migration*).
5. **Der Hardware-Lockup:**  
   Unter der extremen Last lief die SDMA-Transfer-Engine der Grafikkarte in ein Hardware-Timeout (`Fence fallback timer expired`). Da der Desktop-Server (**Xwayland / GNOME**) dieselbe GPU für die Bildschirmausgabe nutzt, riss der GPU-Reset den gesamten Desktop mit in den Abgrund.

---

## 2. Das Kernproblem: Zwei unabhängige KI-Engines auf einer GPU

* **Ollama (llama.cpp / hipBLAS)** und **ComfyUI (PyTorch / ROCm)** wissen **nichts voneinander**.
* Beide Programme prüfen beim Start den freien Speicher der GPU. Wenn Ollama z. B. 24 GB belegt hat, sieht ComfyUI zwar, dass weniger Speicher da ist, versucht aber bei großen Modellen trotzdem, die Gewichte zu laden.
* Während NVIDIA-Karten bei Überbelegung oft mit einer sauberen Fehlermeldung (`CUDA Out of Memory`) abbrechen, neigt der AMD-Kernel-Treiber bei Überbelegung dazu, PCIe-Paging zu starten, was bei Tensoren in dieser Größenordnung zum **System-Freeze** führt.

---

## 3. Die VRAM-Budget-Matrix (Was darf gleichzeitig laufen?)

Deine Karte hat **48 GB physischen Speicher**. Abzüglich 3 GB Sicherheitsreserve für Desktop (Wayland), Browser und Betriebssystem bleiben **45 GB nutzbarer VRAM**.

### Tatsächlicher Speicherbedarf deiner Modelle:

| Typ | Modell | Reiner Modell-VRAM | VRAM inkl. Cache / Puffer |
| :--- | :--- | :--- | :--- |
| **LLM (Sehr groß)** | `qwen3-next-80b` | 42 GB | **~44 GB** (Exklusiv!) |
| **LLM (Groß)** | `artemis-31b` / `qwen3-coder` / `35b` | 30–33 GB | **~35–37 GB** |
| **LLM (Mittel)** | `qwen3-obliterated` (23B) | 23 GB | **~26 GB** |
| **LLM (Kompakt)** | `qwen3.8-27b-q4` | 16 GB | **~18–20 GB** |
| **Video-KI (Sehr groß)**| **Wan 2.1 (14B)** | 28,5 GB + 6,7 GB Text | **~35 GB** (Exklusiv!) |
| **Video-KI (Sehr groß)**| **MiniMax-H3 (Hailuo 03)** | 19,5 GB + 25,3 GB Text | **~35 GB** (Exklusiv!) |
| **Video-KI (Kompakt)** | **LTX-Video 2B** / **SVD-XT** | 5,4–9 GB | **~8–12 GB** |
| **Bild-KI (High-End)** | **FLUX.1 [dev] / [schnell]** | 17,2 GB | **~18 GB** |
| **Bild-KI (Standard)** | **SD 3.5 Large** | 14,9 GB | **~16 GB** |
| **Bild-KI (Kompakt)** | **SDXL Base 1.0** | 6,5 GB | **~7,5 GB** |

---

## 4. Die 3 Betriebsmodi für den Alltag

### 🟢 Modus 1: "Sorgloser Chat & Bildgenerierung im Chat" (Open WebUI)
*Wenn du in Open WebUI ganz normal chattest und nebenbei Bilder generieren lässt:*

* **Kombination A (Kompaktes LLM + FLUX.1):**  
  * LLM: `qwen3.8-27b-q4` (~18 GB)
  * Bild: `flux1-schnell-fp8.safetensors` (~18 GB)
  * **Summe: ~36 GB / 45 GB** $\rightarrow$ **100% grün & absturzsicher!**
* **Kombination B (Großes 32B-LLM + SDXL Base):**  
  * LLM: `qwen3.8-35b-distill` oder `qwen3-coder` (~35 GB)
  * Bild: `sd_xl_base_1.0.safetensors` (~7,5 GB)
  * **Summe: ~42,5 GB / 45 GB** $\rightarrow$ **Stabil im sicheren Rahmen!**

> ⚠️ **Todsünde in Modus 1:**  
> Ein 32B/35B/80B-Modell in Ollama aktiv haben **UND gleichzeitig FLUX.1 (18 GB)** anwerfen. (35 + 18 = 53 GB $\rightarrow$ **Freeze!**)

---

### 🎬 Modus 2: "High-End Video- & Audiogenerierung" (ComfyUI)
*Wenn du Wan 2.1 (14B) oder MiniMax-H3 rendern willst:*

* Wan 2.1 und MiniMax-H3 benötigen **35 GB VRAM** ganz für sich allein.
* **Goldene Regel:** Vor dem Starten eines Video-Workflows **MUSS Ollama entladen werden**!
* Da deine NVMe-SSD das LLM bei der nächsten Chat-Anfrage in **unter 4 Sekunden** wieder in die GPU lädt, verlierst du keine Zeit, gewinnst aber absolute Stabilität.

---

### 🧠 Modus 3: "Große Coding- & Denk-Sessions" (80B LLM)
*Wenn du mit `qwen3-next-80b` (42 GB) arbeitest:*

* Dieses Modell füllt deine 48 GB Karte fast bis zum Rand.
* **Goldene Regel:** In diesem Modus darf **keine Bildgenerierung** parallel laufen.
* Vor Bildgenerierungen kurz `free_vram.sh` ausführen.

---

## 5. Die 4-stufige Schutzarchitektur (Bereits eingerichtet)

### Stufe 1: ComfyUI Hardware-Reserve (`--reserve-vram 3`)
In `image-video-setup/start_comfyui.sh` ist ab sofort der Parameter `--reserve-vram 3` fest hinterlegt:
```bash
exec python main.py --reserve-vram 3 --listen 0.0.0.0 --port 8188
```
* **Effekt:** ComfyUI lässt der Desktop-Oberfläche (Xwayland / GNOME) immer mindestens 3 GB VRAM frei. Selbst wenn ein Workflow an seine Grenzen stößt, friert der Desktop nicht mehr ein.

### Stufe 2: Das 1-Klick-Bereinigungsskript (`free_vram.sh`)
Im Ordner `image-video-setup/` liegt das neue Skript [`free_vram.sh`](file:///home/clemi/Projekte/LLM/image-video-setup/free_vram.sh):
```bash
./free_vram.sh
```
* **Was es tut:**
  1. Stoppt sofort alle aktiven Ollama-Modelle (`ollama stop`).
  2. Sendet ein Signal an ComfyUI (`POST /free`), um ungenutzte PyTorch-Caches freizugeben.
  3. Gibt den VRAM in unter 1 Sekunde komplett auf ~2 GB (Desktop-Standby) frei.

### Stufe 3: Ollama Inaktivitäts-Timeout (`OLLAMA_KEEP_ALIVE=5m`)
* In `/etc/systemd/system/ollama.service` sollte `OLLAMA_KEEP_ALIVE=5m` (oder `10m`) gewählt werden.
* Wenn du im Chat chattest und dann für 5 Minuten nichts tust, räumt Ollama den Speicher automatisch frei – der VRAM steht wieder voll für ComfyUI zur Verfügung.

### Stufe 4: Flow-Matching-Schutz (CFG 1.0)
* Für FLUX.1 ist CFG fest auf **`1.0`** konfiguriert. Dies verhindert nicht nur Bildverbrennungen, sondern halbiert auch den VRAM-Durchsatz pro Rechenschritt.

---

## 6. Praxis-Spickzettel & Notfall-Befehle

| Was willst du tun? | Befehl / Aktion |
| :--- | :--- |
| **VRAM sofort komplett leeren** | `/home/clemi/Projekte/LLM/image-video-setup/free_vram.sh` |
| **VRAM-Auslastung prüfen** | `rocm-smi --showmeminfo vram` |
| **Prüfen, was Ollama im Speicher hat**| `ollama ps` |
| **Ollama gezielt stoppen** | `ollama stop qwen3.8-35b-distill` *(oder welches Modell läuft)* |
| **ComfyUI-Speicher im Browser leeren**| Menü rechts ➔ *Clear Queue* / *Unload Models* |
| **Open WebUI Standard-Bildmodell** | In *Admin ➔ Einstellungen ➔ Bilder*: `flux1-schnell-fp8.safetensors` |

---

### 💡 Faustregel für jeden Tag:
> **Willst du ein Video rendern (Wan oder MiniMax)?**  
> Einmal kurz `./free_vram.sh` ausführen – danach rendert das Video mit Vollgas und ohne jedes Risiko eines Freezes!
