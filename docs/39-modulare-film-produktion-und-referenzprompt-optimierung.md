# 🎬 Leitfaden 39: Modulare Film-Produktion, Referenzprompt-Optimierung & Fehleranalyse

Dieser Leitfaden dokumentiert die Kernmechanismen für professionelle, erweiterbare KI-Langfilm-Produktionen mit **MiniMax H3**, der **AMD Radeon PRO W7800 (48 GB)** und dem **Auto Movie Maker**.

---

## 1. Ursachen-Analyse der aufgetretenen Probleme

### 1.1 Warum brach Szene 4 mit einem 1800s-Timeout ab?
Im Produktionslog fiel auf, dass die GPU während des Samplings von Szene 4 von über 200W auf **73W–76W** abfiel und dort für 28 Minuten verharrte.
* **Ursache:** Szene 4 war die erste **Multi-Charakter-Szene (Two-Shot)**, in der zwei hochauflösende Referenzbilder gleichzeitig im Qwen3-VL Vision-Encoder und MiniMax DiT verarbeitet werden mussten.
* Da in ComfyUI zuvor drei Szenen à 10 Steps gerendert wurden und der interne PyTorch-Cache nicht vollständig bereinigt war (Log-Eintrag: `Using RAM pressure cache`), begann ComfyUI zwischen System-RAM und VRAM zu pagen. Der ROCm-Treiber geriet in einen Memory-Lock, wodurch der 1800s-Sicherheits-Watchdog zuschlug.
* **Behebung:**
  1. Default-Timeout von 1800s auf **2400s (40 Minuten)** erhöht.
  2. AMD ROCm Memory-Allocator via `PYTORCH_HIP_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"` gegen Heap-Fragmentierung gehärtet.

### 1.2 Warum verlangte das Skript am Ende plötzlich ein Sudo-Passwort?
* **Ursache:** Linux-Sudo-Tickets sind standardmäßig auf **15 Minuten** (`timestamp_timeout=15`) begrenzt. Wenn ein Durchlauf durch Timeouts oder lange Renderzeiten länger als 15 Minuten dauert, verfällt das Ticket. Am Skriptende rief die Exit-Trap `sudo ./scripts/w7800_perf_boost.sh auto` auf – und blockierte im Terminal auf Passworteingabe!
* **Behebung:**
  1. `start_sudo_keepalive`: Ein unauffälliger Hintergrundprozess erneuert das Sudo-Ticket automatisch alle 60 Sekunden (`sudo -n true`), solange die Produktion läuft.
  2. Im Exit-Trap wird `sudo -n` verwendet. Selbst falls ein Ticket ungültig wäre, wartet das Skript niemals blockierend auf Tastatureingaben.

### 1.3 Warum wirkte 0.6 MP "nicht besonders hoch" trotz Upscaling?
* **Die Ursache (der Resumed-Scene-Naming-Bug):**
  Beim Analysieren des Produktionslogs von `output/funcontrol_20261016_113110` zeigte sich folgende Warnung für Szenen 1 bis 7:
  ```
  [WARN] Upscaled Clip output/.../szene_001_1080p_ai_1080p.mp4 nicht gefunden -> nutze native Version als Fallback.
  ```
  Beim Resume-Vorgang bereits vorhandener Szenen speicherte das Skript fälschlicherweise den temporären Lanczos-Pfad `szene_001_1080p.mp4`. Beim späteren Zusammensetzen suchte es daher nach `szene_001_1080p_ai_1080p.mp4` – fand diesen nicht und fügte stattdessen den **nicht per KI upgescalten** Clip in den fertigen Gesamtfilm ein!
* **Behebung:**
  In `scripts/auto_movie_maker.py` wurde die Pfadverwaltung korrigiert: `rendered_scene_files` speichert immer die sauberen nativen Clips `szene_001.mp4`. Das Post-Flight-Upscaling holt sich garantiert alle echten Real-ESRGAN-Super-Resolution-Clips (`szene_001_ai_1080p.mp4`).

---

## 2. Der optimierte Master-Referenzprompt (`krimi_story_1min_2personen.yaml`)

Ein konsistenter KI-Film benötigt drei feste Säulen:
1. **Master-Style-Anker:** Definiert Kamera, Filmkorn, Belichtung und Farbwelt einheitlich für alle Szenen.
2. **Explizites Charakter-Tagging:** Jede Szene deklariert exakt, wer zu sehen ist (`<Picture 1>`, `<Picture 2>` oder beide).
3. **Kausale Handlungskette (Keine Loops):** Jede Szene schließt nahtlos an die Konsequenz der vorherigen Szene an.

### 2.1 Der Master-Style-Header
```yaml
master_style: >-
  Master Cinematic Look: High-end neo-noir crime thriller aesthetic, shot on 35mm Arri Alexa 65 anamorphic lenses (2.39:1 widescreen frame), shallow depth of field, natural motion blur, authentic 35mm film grain.
  Atmosphere & Lighting: Volumetric atmospheric rain, drifting steam, high-contrast chiaroscuro shadows contrasted with vibrant cyan, amber and crimson neon reflections on polished black marble and floor-to-ceiling glass.
  Character Fidelity & Anatomy: Exact photorealistic facial and wardrobe replication from reference images (<Picture 1> Detective Cross: rugged 45yo male, drenched charcoal fedora, dark trenchcoat, stubbled square jaw. <Picture 2> Elena Vance: agile 30yo female, high-collar matte-black tactical coat with glowing cyan circuit seams, sleek dark hair with wet strands).
  Temporal Progression: Every shot advances forward in time without looping or repeating actions.
```

### 2.2 Kausale Dramaturgie statt Aktionswiederholung
* **Bisheriges Problem:** Szene N zeigte Elena, wie sie den Kristall wirft. Szene N+1 begann neutral und zeigte erneut den Wurf.
* **Optimierte Kausalkette:**
  * **Szene 7 (Wurf):** Elena wirft den leuchtenden Datenkristall flach über das Parkett und sprintet zur Balkontür.
  * **Szene 8 (Reaktion):** Detective Cross geht reflexartig aufs Knie, fängt den rotierenden Kristall am Boden ab und blickt wütend auf, als er die Finte begreift.
  * **Szene 9 (Auf der Brüstung):** Elena schwingt sich im strömenden Regen auf das Glasgeländer und salutiert spöttisch.
  * **Szene 10 (Verfolgung):** Cross stürmt durch die zersplitterten Schiebetüren auf die Terrasse und hechtet zum Geländer.
  * **Szene 11 (Der Sprung):** Elena stürzt sich rücklings in die Häuserschlucht; der Wingsuit-Fallschirm öffnet sich.
  * **Szene 12 (Finale):** Cross steht allein im Regen an der Brüstung, blickt auf den pulsierenden Datenkristall in seiner Hand.

---

## 3. Modulare Filmentwicklung: Szenen anhängen, austauschen & schneiden

### 3.1 Szenen hinten anhängen (Endlos-Erweiterung)
Möchtest du einen bestehenden 60-Sekunden-Film auf 90 oder 120 Sekunden erweitern:
1. Öffne die Story-YAML (`configs/krimi_story_1min_2personen.yaml`) und füge einfach weitere Szenen an (`id: 13`, `id: 14`, etc.).
2. Starte die Pipeline unter Angabe desselben Ausgabeordners:
   ```bash
   ./scripts/run_1min_movie.sh --story configs/krimi_story_1min_2personen.yaml --output output/mein_projekt
   ```
3. **Was passiert?**
   * Die vorhandenen Szenen 1 bis 12 werden in Sekundenbruchteilen übersprungen (`[OK] Clip bereits gerendert -> Überspringe Rendering!`).
   * Nur die neuen Szenen 13+ werden gerendert.
   * Am Ende fügt das Skript **alle** Szenen (z. B. 1–15) zum neuen Gesamtfilm zusammen.

### 3.2 Gezielter Szenen-Austausch (`--rerun-scenes`)
Wenn eine Szene (z. B. Szene 4) anatomisch ungenau war oder dir der Kamerawinkel nicht gefällt:
* **Methode A (Über die CLI mit dem neuen Flag):**
  ```bash
  ./scripts/run_1min_movie.sh --output output/mein_projekt --rerun-scenes 4
  ```
  *(Oder mehrere Szenen kommagetrennt: `--rerun-scenes 4,7`)*
  Das Skript löscht automatisch nur die alten Versionen dieser Szenen, rendert sie frisch neu und aktualisiert den Gesamtfilm.
* **Methode B (Manuell per Dateisystem):**
  Lösche die betreffende Datei im Projektordner:
  ```bash
  rm output/mein_projekt/szene_004.mp4 output/mein_projekt/szene_004_ai_1080p.mp4
  ```
  Beim nächsten Start erkennt `resume`, dass Szene 4 fehlt, rendert nur diese und schneidet den Film neu.

### 3.3 Sofortiges Gesamtfilm-Remastering (`--concat-only`)
Wenn du Szenen extern nachbearbeitet hast, ein Audiobett austauschen willst oder harte Schnitte vs. weiche Überblendungen testen möchtest **ohne neu zu rendern**:
```bash
./scripts/run_1min_movie.sh --output output/mein_projekt --concat-only --hard-cuts
```
*(Funktioniert in 5 Sekunden – und erfordert nicht einmal, dass ComfyUI gestartet ist!)*

---

## 4. Qualität & Stabilität: 0.6 MP vs. 0.7 MP Sweet-Spot

| Profil | Auflösung | Steps | Zeit pro Clip | Detailgrad | Stabilität (W7800) |
|---|---|---|---|---|---|
| **0.6 MP Turbo (Empfohlen)** | 1056x608 | 4–6 | ~4–6 Min | Sehr hoch (mit Real-ESRGAN SSAA) | 100% Felsenfest |
| **0.7 MP Turbo** | 1152x640 | 4–6 | ~7–9 Min | Exzellent | Stabil mit `PYTORCH_HIP_ALLOC_CONF` |
| **0.6 MP Native Cinema** | 1056x608 | 20 (`--no-turbo`) | ~18–20 Min | Festival-Qualität, Mikro-Poren | 100% Felsenfest |

> [!TIP]
> **Wichtig für maximale Bildschärfe:**
> Verwende bei Turbo-LoRA **4 bis maximal 6 Steps** (nicht 10 Steps). Turbo-LoRAs sind Destillationen; bei 10 Steps verfünffacht sich die Renderzeit ohne Detailgewinn. Echte 1080p-Mikroschärfe entsteht durch das Post-Flight **Real-ESRGAN SSAA** (4x Neural Super-Resolution mit Unsharp-Maske).

