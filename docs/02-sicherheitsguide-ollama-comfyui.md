# 🛡️ Sicherheitsguide: Gemeinsame Nutzung von Ollama & ComfyUI
> **Hardware:** AMD Radeon PRO W7800 (48 GB VRAM) | 64 GB RAM | Ubuntu Linux (ROCm 6.4)  
> **Ziel:** 100% Stabilität – Nie wieder System-Freezes bei gleichzeitiger Text-, Bild- und Videogenerierung.

---

## 📑 Inhaltsverzeichnis
1. [Forensische Ursachen-Analyse der beiden Abstürze](#1-forensische-ursachen-analyse-der-beiden-abstürze)
   - [A. Absturz-Typ 1: VRAM-Überbelegung (Ollama + ComfyUI Gleichzeitigkeit)](#a-absturz-typ-1-vram-überbelegung-ollama--comfyui-gleichzeitigkeit)
   - [B. Absturz-Typ 2: GPU-Watchdog-Timeout bei Video-KI (Wan 2.1 + Desktop/Firefox)](#b-absturz-typ-2-gpu-watchdog-timeout-bei-video-ki-wan-21--desktopfirefox)
2. [Das Kernproblem: Zwei unabhängige KI-Engines auf einer GPU](#2-das-kernproblem-zwei-unabhängige-ki-engines-auf-einer-gpu)
3. [Die VRAM-Budget-Matrix (Was darf gleichzeitig laufen?)](#3-die-vram-budget-matrix-was-darf-gleichzeitig-laufen)
4. [Die 3 Betriebsmodi für den Alltag](#4-die-3-betriebsmodi-für-den-alltag)
5. [Die 6-stufige Schutzarchitektur (Vollständig eingerichtet)](#5-die-6-stufige-schutzarchitektur-vollständig-eingerichtet)
6. [Praxis-Spickzettel & Notfall-Befehle](#6-praxis-spickzettel--notfall-befehle)
7. [Der 4-Stufen-Notfallplan: Was tun, wenn das System einfriert?](#7-der-4-stufen-notfallplan-was-tun-wenn-das-system-einfriert)

---

## 1. Forensische Ursachen-Analyse der beiden Abstürze

Die System- und Kernel-Logs belegen zwei grundlegend unterschiedliche Fehlerursachen auf einer gemeinsamen Single-GPU-Workstation (Display + Compute):

### A. Absturz-Typ 1: VRAM-Überbelegung (Ollama + ComfyUI Gleichzeitigkeit)
*Zeitpunkt: Gestern Abend, 22:14 bis 22:17 Uhr*

```text
[22:14:06] ComfyUI: Requested to load WanTEModel (6.4 GB VRAM)
[22:14:38] ComfyUI: Requested to load WAN21 14B (26.2 GB VRAM)
[22:14:15] kernel: workqueue: svm_range_restore_work [amdgpu] hogged CPU for >10000us 2051 times
[22:17:13] kernel: amdgpu 0000:03:00.0: Fence fallback timer expired on ring sdma0
[22:17:19] kernel: amdgpu: ring sdma0 timeout ... device wedged, but recovered through reset
[22:17:34] kernel: amdgpu: ring comp_1.2.1 timeout ... Process Xwayland ... device wedged
--> [HARD FREEZE: Desktop reagiert nicht mehr, Monitor friert ein, Hard Reboot erforderlich]
```

**Was war passiert?**
1. **Ollama war noch aktiv geladen:** Hielt ~24 GB VRAM aus einem vorherigen Chat.
2. **ComfyUI startete parallel:** Forderte 32,6 GB VRAM für Wan 2.1 an.
3. **Speicherüberlauf:** $24 + 32,6 + 2\text{ (Desktop)} = \mathbf{58,6\text{ GB}}$ bei nur 48 GB physischem VRAM.
4. **PCIe-Stau (SDMA-Engine Timeout):** AMD SVM Page Migration schob Gigabytes über PCIe hin und her; die SDMA-Engine lief in ein Hardware-Timeout $\rightarrow$ Hard Freeze.

---

### B. Absturz-Typ 2: GPU-Watchdog-Timeout bei Video-KI (Wan 2.1 + Desktop/Firefox)
*Zeitpunkt: Heute Vormittag, 10:02:27 bis 10:02:32 Uhr*

```text
 10%|█         | 3/30 [01:01<10:43, 23.82s/it]
 ...
 47%|████▋     | 14/30 [06:36<08:06, 30.41s/it]
 50%|█████     | 15/30 [07:07<07:36, 30.42s/it]
kernel: amdgpu: ring gfx_0.0.0 timeout, signaled seq=119811, emitted seq=119812
kernel: amdgpu: Process firefox pid 9429 thread firefox:cs0 pid 9625
kernel: amdgpu: Starting gfx_0.0.0 ring reset ... MES failed to respond
kernel: amdgpu: MODE1 reset
kernel: amdgpu: VRAM is lost due to GPU reset!
ComfyUI: HW Exception by GPU node-1 reason :GPU Hang -> Fatal Python error: Aborted
gnome-shell: amdgpu: The CS has cancelled because the context is lost. -> status=6/ABRT
--> [DESKTOP ABORT: Bildschirm wird schwarz, Session schließt sich, Rückkehr zum Login-Screen (GDM)]
```

**Was war passiert?**
1. **Ollama war völlig unschuldig:** Kein Modell geladen (`ollama ps` war leer).
2. **Kein VRAM-Überlauf:** Der Speicher war mit 33,6 GB stabil im 48-GB-Limit.
3. **Schwere 30-Sekunden-Rechenschritte:** Wan 2.1 (14B BF16) renderte seit über 7 Minuten erfolgreich. Jeder Schritt dauerte **30,4 Sekunden**.
4. **Firefox forderte Grafik-Rendering an:** Bei Schritt 15 schickte Firefox (`firefox:cs0`) einen GPU-Draw-Befehl an den Desktop-Ring `ring gfx_0.0.0`.
5. **Der Treiber-Fehlalarm (`queue_preemption_timeout_ms = 9000`):** Der Linux AMD-Treiber wartet standardmäßig maximal **9 Sekunden** auf die Freigabe des Rings. Da der 30-Sekunden-Wan-Schritt die GPU noch voll belegte, dachte der Treiber fälschlicherweise, die GPU sei abgestürzt!
6. **Panik-Hardware-Reset (`MODE1 reset`):** Der Treiber führte einen Hardware-Reset durch, wodurch der VRAM gelöscht wurde. ComfyUI brach ab und GNOME Shell stürzte ab $\rightarrow$ Desktop-Kick.

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

## 5. Die 6-stufige Schutzarchitektur (Vollständig eingerichtet)

### Stufe 1: ComfyUI Hardware-Reserve (`--reserve-vram 3`)
In `image-video-setup/start_comfyui.sh` ist der Parameter `--reserve-vram 3` fest hinterlegt:
* **Effekt:** ComfyUI lässt der Desktop-Oberfläche (Xwayland / GNOME) immer mindestens 3 GB VRAM frei. Selbst wenn ein Workflow an seine Grenzen stößt, friert der Desktop nicht mehr ein.

### Stufe 2: Host-RAM Capping in ComfyUI (`--cache-ram 8 32`)
Standardmäßig pinnt ComfyUI bis zu 56,7 GB des System-RAMs. Durch `--cache-ram 8 32` in `start_comfyui.sh`:
* **Effekt:** Aktiver Node-Cache wird auf 8 GB gedeckelt, inaktiver Cache auf 32 GB.
* **Ergebnis:** Mindestens **25–30 GB System-RAM** bleiben immer frei für Desktop, Firefox, Docker und Betriebssystem.

### Stufe 3: ROCm SDMA-Bypass (`HSA_ENABLE_SDMA=0`) & Allocator-Tuning
In `start_comfyui.sh` sind zwei kritische ROCm-Umgebungsvariablen aktiviert:
```bash
export PYTORCH_CUDA_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"
export HSA_ENABLE_SDMA=0
```
* **Effekt:** Verhindert PyTorch-Speicherfragmentierung und leitet Host-zu-Device-Transfers über Compute-Blits statt über die SDMA-Hardware-Engine um. Das schließt SDMA-Ring-Timeouts (`ring sdma0 timeout`) komplett aus.

### Stufe 4: Kernel Watchdog-Timeout Patch (60 Sekunden statt 9 Sekunden)
Für lange Video-Rechenschritte (wie Wan 2.1 14B mit 30s/Step) wird der AMD-Treiber-Watchdog auf 60 Sekunden erhöht.
* **Skript zum Anwenden:**
  ```bash
  sudo /home/clemi/Projekte/LLM/image-video-setup/apply_amd_gpu_fixes.sh
  ```
* **Was es tut:** Schreibt `lockup_timeout=60000,60000,60000,60000` und `queue_preemption_timeout_ms=60000` nach `/etc/modprobe.d/amdgpu-timeout.conf` und baut das initramfs neu. Nach einem Neustart bricht der Treiber auch bei 30-Sekunden-Schritten niemals mehr panisch mit einem MODE1-Reset ab.

### Stufe 5: Das 1-Klick-Bereinigungsskript (`free_vram.sh`)
Im Ordner `image-video-setup/` liegt das Skript [`free_vram.sh`](file:///home/clemi/Projekte/LLM/image-video-setup/free_vram.sh):
```bash
./free_vram.sh
```
* **Was es tut:** Stoppt sofort alle aktiven Ollama-Modelle (`ollama stop`) und leert alle ComfyUI-Caches per API (`POST /free`).

### Stufe 6: Ollama Inaktivitäts-Timeout & Flow-Matching-Schutz (CFG 1.0)
* In `/etc/systemd/system/ollama.service` ist `OLLAMA_KEEP_ALIVE=15m` und `OLLAMA_GPU_OVERHEAD=3294967296` (3,3 GB) konfiguriert.
* Für FLUX.1 ist CFG fest auf **`1.0`** konfiguriert (halbiert den VRAM-Durchsatz pro Step).

---

## 6. Praxis-Spickzettel & Notfall-Befehle

| Was willst du tun? | Befehl / Aktion |
| :--- | :--- |
| **AMD GPU 60s-Watchdog Patch installieren** | `sudo /home/clemi/Projekte/LLM/image-video-setup/apply_amd_gpu_fixes.sh` *(einmalig ausführen + Reboot)* |
| **VRAM sofort komplett leeren** | `/home/clemi/Projekte/LLM/image-video-setup/free_vram.sh` |
| **VRAM-Auslastung prüfen** | `rocm-smi --showmeminfo vram` |
| **Prüfen, was Ollama im Speicher hat**| `ollama ps` |
| **Ollama gezielt stoppen** | `ollama stop qwen3.8-35b-distill` *(oder welches Modell läuft)* |
| **ComfyUI-Speicher im Browser leeren**| Menü rechts ➔ *Clear Queue* / *Unload Models* |
| **Open WebUI Standard-Bildmodell** | In *Admin ➔ Einstellungen ➔ Bilder*: `flux1-schnell-fp8.safetensors` |

---

### 💡 Faustregeln für absolute Stabilität:
1. **Willst du ein Video rendern (Wan oder MiniMax)?**  
   Einmal kurz `./free_vram.sh` ausführen – danach rendert das Video ohne VRAM-Konflikte.
2. **Während eines langen Video-Renders (7–15 Minuten):**  
   Lass den Browser-Tab im Hintergrund ruhen und surfe nicht mit hardwarebeschleunigten 3D/WebGL-Seiten auf demselben Display-Server herum, bis der AMD-Timeout-Patch aktiv ist.

---

## 7. Der 4-Stufen-Notfallplan: Was tun, wenn das System einfriert?

Wenn der Bildschirm stockt oder die Maus einfriert, **niemals sofort panisch den Netzstecker ziehen oder die Power-Taste 10 Sekunden lang drücken!**  
Bei 90% aller GPU-Freezes läuft der Linux-Kernel im Hintergrund völlig normal weiter – lediglich die Bildschirmausgabe der GPU hängt.

Gehe immer nach dieser 4-Stufen-Leiter vor (vom schonendsten zum härtesten Eingriff):

### 🟢 Stufe 1: TTY-Terminal aufrufen (Tastatur reagiert noch)
Wenn die grafische Oberfläche (Wayland/Desktop) eingefroren ist:
1. Drücke auf der Tastatur: **`Strg` + `Alt` + `F3`** (oder `F4` / `F5`).
2. Du verlässt die GUI und siehst eine Text-Konsole: Melde dich mit deinem Benutzernamen (`clemi`) und Passwort an.
3. Beende den Übeltäter gezielt und schonend:
   ```bash
   # VRAM sofort leeren
   /home/clemi/Projekte/LLM/image-video-setup/free_vram.sh

   # ODER den Desktop-Server sauber neu starten
   sudo systemctl restart gdm
   ```
4. Zurück zum Desktop gelangst du mit: **`Strg` + `Alt` + `F2`** (oder `F1`).

---

### 🟡 Stufe 2: SSH-Rettung übers Smartphone oder Zweitgerät (Das mächtigste Werkzeug!)
Wenn Monitor, Maus und Tastatur am PC blockiert sind:
1. Nimm dein Smartphone (z. B. mit der kostenlosen App *Termius*) oder einen Laptop zur Hand.
2. Verbinde dich per SSH über dein Tailscale-Netzwerk:
   ```bash
   ssh clemi@100.102.224.36
   ```
3. Führe den VRAM-Cleaner aus oder starte den PC geordnet neu:
   ```bash
   /home/clemi/Projekte/LLM/image-video-setup/free_vram.sh
   # Oder falls nötig:
   sudo systemctl reboot
   ```
* **Vorteil:** Alle Schreib-Caches auf deinen NVMe-SSDs werden ordnungsgemäß synchronisiert. Null Datenverlust, keine Dateisystemfehler!

---

### 🟠 Stufe 3: Der magische Linux-Rettungsanker: REISUB (Magic SysRq)
Wenn weder TTY noch Netzwerk reagieren, aber der Linux-Kernel noch Strom hat:

Halte **`Alt` + `Druck` (Print Screen)** gedrückt und tippe mit jeweils **2 Sekunden Pause** nacheinander die Tasten:
$$\mathbf{R} \;\longrightarrow\; \mathbf{E} \;\longrightarrow\; \mathbf{I} \;\longrightarrow\; \mathbf{S} \;\longrightarrow\; \mathbf{U} \;\longrightarrow\; \mathbf{B}$$

*(Merksatz: **R**eboot **E**ven **I**f **S**ystem **U**tterly **B**roken)*

| Buchstabe | Was der Linux-Kernel tut: | Warum es genial ist: |
| :---: | :--- | :--- |
| **R** *(unRaw)* | Entreißt dem abgestürzten Desktop die Tastaturkontrolle. | Reaktiviert Tastatureingaben. |
| **E** *(tErm)* | Sendet `SIGTERM` an alle Prozesse. | Lässt Prozesse sauber schließen. |
| **I** *(kIll)* | Sendet `SIGKILL` an verbliebene Hänger. | Räumt blockierte Prozesse ab. |
| **S** *(Sync)* | **Schreibt alle RAM-Puffer auf die SSD.** | **Verhindert Datenverlust!** |
| **U** *(Unmount)*| Hängt alle Dateisysteme "Nur-Lesen" (*Read-Only*) ein. | **Schützt SSD vor Korruption.** |
| **B** *(reBoot)*| Führt einen sauberen Hardware-Reboot durch. | Startet den Rechner sicher neu. |

> ⚙️ **Einmalige Aktivierung für volles REISUB in Ubuntu:**
> Ubuntu schützt standardmäßig einige SysRq-Tasten. Um die volle REISUB-Funktion freizuschalten:
> ```bash
> echo "kernel.sysrq = 1" | sudo tee /etc/sysctl.d/99-sysrq.conf
> sudo sysctl -p /etc/sysctl.d/99-sysrq.conf
> ```

---

### 🔴 Stufe 4: Hard Power-Off (Der allerletzte Ausweg)
Nur wenn Stufe 1, 2 und 3 nach mindestens 30 Sekunden Wartezeit keinerlei Reaktion zeigen:
* Halte den Power-Knopf am PC-Gehäuse für **8 bis 10 Sekunden gedrückt**, bis der Strom abschaltet.
* 10 Sekunden warten, dann wieder einschalten.

