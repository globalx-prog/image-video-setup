# Leitfaden: Wann Modelle entladen werden sollten (und wann NICHT)

## 1. Wichtigste Grundregel:
* **Wenn du durchgängig mit EINEM Modell arbeitest, das in 48 GB passt:**  
  👉 **VRAM-Cleanup ist VÖLLIG UNNÖTIG (und verlangsamt die Arbeit massiv)!**  
  * **Betrifft:** **Wan 2.1**, **Wan 2.2**, **FLUX.1 [dev]**, **SDXL** und **Qwen-Image-2.1**.  
  * **Die Speicher-Realität:** Jedes dieser Modelle belegt zwischen 6 GB (SDXL) und maximal 38 GB (Wan 2.2). Auf deiner AMD Radeon PRO W7800 (48 GB VRAM) passen alle Komponenten dauerhaft und zu **100 % in den Grafikspeicher**.  
  * **Großer Vorteil:** Wenn kein Cleanup-Knoten die Gewichte löscht, verbleiben sie im VRAM. Folge-Generierungen (neue Prompts, Seeds, Posen) starten in **0 Sekunden** ohne jegliche Ladezeit!  
  * **Nachteil von unnötigem Cleanup:** Jedes Mal müssen gigantische Modelldateien (z. B. 26–31 GB bei Wan oder 24 GB bei Flux) neu von der SSD geladen werden – das kostet bei jedem Klick 20 bis 60 Sekunden sinnlose Wartezeit.

---

## 2. Wann VRAM-Cleanup tatsächlich sinnvoll & notwendig ist:

1. **Nur bei einem MODELL-WECHSEL:**
   * Wenn du von Wan zu einem anderen Modell (z. B. **MiniMax H3** oder **FLUX.1 [dev]**) wechselst.
   * **Warum:** Um alten Speicherplatz restlos freizugeben, damit das neue Modell unfragmentierten Speicher vorfindet.
2. **Bei MiniMax H3 nach dem Bildladen (Konditionierung):**
   * MiniMax nutzt den gigantischen 26 GB Text- & Bild-Encoder (`qwen3vl_32b`). Zusammen mit dem 20 GB DiT übersteigt das Gesamtgewicht die 48 GB VRAM.
   * Der 26 GB VLM-Encoder muss nach der Bildanalyse weichen, um Platz für den Diffusionskern zu machen.
   * Nach Fertigstellung des Videos sollte MiniMax entladen werden, damit der Encoder nicht dauerhaft im System-RAM verweilt.

---

## 3. Methoden zur Speicherverwaltung in der Praxis:

### Weg 1: Der "Unload Models" Button im Web-Interface (Empfohlen bei Modellwechsel)
* Im ComfyUI-Menü oben rechts auf **`Unload Models`** klicken.
* Gibt alle Gewichte sofort aus VRAM und System-RAM frei, ohne den Server neu zu starten.

### Weg 2: Im Workflow über Knoten (`VRAM-Cleanup`)
* **Für reine Wan-Workflows:** **Knoten ENTFERNEN!**
* **Für MiniMax H3 Workflows:** Am Ende des Workflows (hinter dem Video-Save-Knoten) kann ein Cleanup-Knoten geschaltet werden, um den 26 GB Encoder nach dem Run aus dem RAM zu entfernen.

### Weg 3: Über Startparameter in `start_comfyui.sh`
* In `start_comfyui.sh` ist `--cache-ram 4 16` aktiv:
  * Begrenzt inaktive Modelle im System-RAM auf maximal 16 GB.
  * Verhindert zuverlässig, dass MiniMax den 64 GB System-RAM überfüllt und Swap-Freezes auf der SSD auslöst.

### Weg 4: Sofortiger Quick-Restart & VRAM-Reset per Terminal
Wenn ein Modell hängt oder du den Dienst komplett frisch starten willst:

```bash
cd /home/clemi/Projekte/LLM/image-video-setup
./restart_comfyui.sh
```
* Startet den Systemd-Service `comfyui.service` sauber neu.
* Gibt die vollen 48 GB VRAM auf Treiberebene frei.
* Zeigt direkt die Live-Logs via `journalctl -f` an.

### Weg 5: All-in-One Speicherbereiniger `./free_vram.sh` (VRAM + RAM + Swap)
Wenn du ComfyUI **nicht neu starten**, aber VRAM, System-RAM und Swap auf einen Schlag befreien willst:

```bash
cd /home/clemi/Projekte/LLM/image-video-setup
./free_vram.sh
```
* Entlädt Ollama- und ComfyUI-Modelle aus dem VRAM.
* Leert inaktive Linux Dateisystem-Caches.
* Holt den SSD-Swap sofort zurück in den physischen RAM (`swapoff && swapon`).


---

## 4. Problembehebung: Warum laggt das System TROTZ VRAM-Freigabe? (Das Swap-Phänomen)

### Die Ursache: VRAM vs. System-RAM & SWAP
Wenn du nach einem MiniMax H3 Run auf `Unload Models` klickst, wird zwar der **GPU-VRAM** geleert, das System ruckelt aber trotzdem. 

**Der Grund:**
1. MiniMax H3 benötigt kurzzeitig extrem viel **System-RAM (Host-Arbeitsspeicher)**, um Text-Encoder, DiT und Audio-VAE zu handhaben.
2. Um einen Speicherabsturz (OOM) zu verhindern, hat der Linux-Kernel während des Runs deine **Desktop-Programme** (GNOME/KDE, Browser-Tabs, Fenstermanager, UI-Compositor) auf die **SSD in die Swap-Partition ausgelagert**.
3. **Das Linux-Verhalten:** Nach der Generierung holt Linux diese Daten **nicht automatisch** zurück in den RAM! Bei jeder Mausbewegung und jedem Klick muss die CPU die Fenster-Daten erst mühsam von der SSD nachladen (hohe I/O-Latenz, "Page Faults").
4. Zudem hält der Python-Prozess von ComfyUI im Host-RAM oft noch 15–20 GB reservierten Speicherplatz (glibc / PyTorch Allocator).

### Die 2-Schritt-Sofortlösung (dauert 5 Sekunden):

1. **ComfyUI-Dienst neustarten** (gibt den Host-RAM auf Betriebssystemebene frei):
   ```bash
   systemctl --user restart comfyui.service
   ```
   *(oder `./restart_comfyui.sh`)*

2. **Den Swap zurück in den schnellen RAM holen** (leert die SSD-Auslagerung sofort):
   ```bash
   sudo swapoff -a && sudo swapon -a
   ```
   *Dauert ca. 5 Sekunden. Sobald der Befehl durch ist, liegt dein gesamtes Betriebssystem wieder zu 100 % im blitzschnellen physischen RAM, und das Ruckeln ist sofort vollständig verschwunden!*

### Wichtiger Hinweis zum Knoten `VRAM-Cleanup`:
Der ComfyUI-Knoten `VRAM-Cleanup` ruft intern `torch.cuda.empty_cache()` und `unload_all_models()` auf:
* ✅ Er leert die **Grafikkarte (VRAM)** zu 100 %.
* ⚠️ Er leert **NICHT** den **System-RAM** (wird durch glibc Heap-Fragmentierung im Python-Prozess gehalten).
* ❌ Er leert **NIEMALS** den **Swap** (Swap gehört dem Linux-Kernel; Python hat keine Root-Rechte, um den Kernel-Swap zu leeren).

Deshalb hilft der Knoten zwar gegen VRAM-Überläufe, kann aber ein Desktop-Ruckeln nach zu großen Modelläufen nicht verhindern.

### 🛡️ Dauerhafte Vollautomatisierung: Die Sudoers-Regel
Damit Hintergrunddienste (`auto-swap-reclaim.timer`), Skripte (`./free_vram.sh`) und ComfyUI-Hooks den Swap künftig **ohne Passwortabfrage** leeren dürfen, ist folgende Regel in `/etc/sudoers.d/ai-swap-reclaim` hinterlegt:

```bash
# Erlaubt dem KI-Benutzer swapoff/swapon ohne Passwort:
clemi ALL=(ALL) NOPASSWD: /usr/sbin/swapoff, /usr/sbin/swapon
```

* **Vorteil:** Sobald nach einer Arbeitsspitze wieder RAM frei wird, leert der automatische Wächter den Swap vollautomatisch und leise im Hintergrund. Du musst nie wieder ein Passwort eingeben oder manuell `swapoff` tippen!

> [!TIP]
> Die detaillierten Messwerte, warum 0.4 und 0.5 die idealen Sweet-Spots für MiniMax H3 sind und warum 0.8 zum Absturz führt, findest du in der [**Stabilitäts- & Auflösungsmatrix**](file:///home/clemi/Projekte/LLM/image-video-setup/SPEICHER_UND_AUFLOESUNG_MATRIX.md).