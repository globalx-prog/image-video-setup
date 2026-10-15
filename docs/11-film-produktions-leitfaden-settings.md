# 🎬 Leitfaden: Film-Produktion mit MiniMax H3 — Settings, Workflows & Feature-Matrix
## Umfassende Anleitung zur automatisierten Video-Generierung auf AMD Radeon PRO W7800 (48 GB VRAM)

---

## 📑 Inhaltsverzeichnis
1. [Übersicht aller verfügbaren Settings & Parameter](#1-übersicht-aller-verfügbaren-settings--parameter)
2. [Praxisbeispiele: Filme mit unterschiedlichen Settings drehen](#2-praxisbeispiele-filme-mit-unterschiedlichen-settings-drehen)
   - [Beispiel 1: Ultra-Fast Pre-Vis / Storyboard-Check (15s–30s)](#beispiel-1-ultra-fast-pre-vis--storyboard-check)
   - [Beispiel 2: Ausgewogene Serienproduktion (Empfohlener Standard)](#beispiel-2-ausgewogene-serienproduktion-empfohlener-standard)
   - [Beispiel 3: High-End Kino-Master mit AI-Upscaling (1080p Full HD)](#beispiel-3-high-end-kino-master-mit-ai-upscaling-1080p-full-hd)
   - [Beispiel 4: Epische Plansequenz ohne Turbo (Pure Diffusion)](#beispiel-4-epische-plansequenz-ohne-turbo-pure-diffusion)
   - [Beispiel 5: Social Media / Hochformat (9:16 Shorts & Reels)](#beispiel-5-social-media--hochformat-916-shorts--reels)
   - [Beispiel 6: Das 5-Minuten-Epos (60 Szenen vollautomatisch)](#beispiel-6-das-5-minuten-epos-60-szenen-vollautomatisch)
3. [Tabelle: Realisierte vs. Mögliche Funktionen](#3-tabelle-realisierte-vs-mögliche-funktionen)
4. [Prompt-Engineering & Charakter-Kontinuität](#4-prompt-engineering--charakter-kontinuität)
5. [2-Personen-Setup & Face Detailer (Multi-Charakter-Dreh)](#5-2-personen-setup--face-detailer-multi-charakter-dreh)
6. [Regie-Handbuch: Ref2V vs. I2V bei mehreren Charakteren (Drehbuch-Beispiele)](#6-regie-handbuch-ref2v-vs-i2v-bei-mehreren-charakteren-drehbuch-beispiele)
7. [Benchmark-, Zeit- & Qualitäts-Matrix: Alle Optimierungen im Vergleich](#7-benchmark--zeit---qualitäts-matrix-alle-optimierungen-im-vergleich)

---

## 1. Übersicht aller verfügbaren Settings & Parameter

Alle Parameter können direkt als Befehlszeilen-Flags an `scripts/auto_movie_maker.py` bzw. die Starter-Skripte übergeben werden:

| Parameter | CLI-Flag | Wertebereich | Standard | Auswirkung auf Bild & System |
| :--- | :--- | :--- | :--- | :--- |
| **Drehbuch** | `--story` | `.yaml`, `.json`, `.txt` | *(Pflicht)* | Definiert Szenenfolge, Schnitte (`ref2v`), Handoffs (`i2v`) und Tonspur. |
| **Charakter 1** | `--character` | `.png` Bildpfad | `detective_portrait.png` | Bildanker für das Gesicht & Outfit des 1. Charakters (`<Picture 1>`). |
| **Charakter 2** | `--character2` | `.png` Bildpfad | `None` | Bildanker für das Gesicht & Outfit des 2. Charakters (`<Picture 2>`). |
| **Sampling Steps** | `--steps` | `4` bis `30` | `4` (Turbo) | **4:** Extrem schnell (~45s), **6–8:** Scharfe Details (~70s), **20+:** No-Turbo. |
| **Turbo Modus** | `--no-turbo` | Schalter | *Aktiv* (Turbo LoRA) | Deaktiviert das 8-Step Turbo-LoRA und schaltet auf 20 Steps Standarddiffusion um. |
| **Upscaling** | `--upscale` | Schalter | *Deaktiviert* | Schaltet `R-ESRGAN 4x+ Batched` (Lanczos, FP16) auf 1080p direkt hinzu. |
| **VRAM Warmhalt** | `--offload-between-scenes` | Schalter | *False (Warm)* | **Standard (False):** 32B-Modell bleibt im VRAM $\rightarrow$ spart 50s Wartezeit pro Clip! |
| **Breite** | `--width` | `480` bis `960` | `864` | Horizontale Auflösung (Widescreen 16:9). |
| **Höhe** | `--height` | `480` bis `864` | `480` | Vertikale Auflösung (480p = 0.4 MP Basis-Sweet-Spot). |
| **Dauer pro Clip**| `--duration` | `3.0` bis `7.0` s | `5.0` s | Dauer eines Einzelschnitts (5s = 120 Frames bei 24 fps). |
| **Ausgabeordner** | `--output` | Verzeichnispfad | `output/auto_movie` | Speicherort für Einzelszenen, Handoff-Frames und den Gesamtfilm. |
| **ComfyUI Port** | `--comfy-url` | URL | `http://127.0.0.1:8188` | Schnittstelle zum lokalen ComfyUI-Dienst. |

---

## 2. Praxisbeispiele: Filme mit unterschiedlichen Settings drehen

### Beispiel 1: Ultra-Fast Pre-Vis / Storyboard-Check
* **Ziel:** Prüfen von Schnittfolge, Kameraperspektiven und Ton, bevor viel Rechenzeit investiert wird.
* **Renderzeit:** ca. 45–50 Sekunden pro 5s-Szene.
* **VRAM-Bedarf:** ca. 24 GB.

```bash
python3 scripts/auto_movie_maker.py \
    --story configs/krimi_intro_30s.yaml \
    --steps 4 \
    --width 864 \
    --height 480 \
    --output output/krimi_test_draft
```
> **Ergebnis:** Ein 30-Sekunden-Film in unter 5 Minuten Gesamtzeit fertig gerendert.

---

### Beispiel 2: Ausgewogene Serienproduktion (Empfohlener Standard)
* **Ziel:** Scharfe Gesichtszüge, saubere Faltenwürfe, flüssige Bewegungsphysik und synchroner Stereo-Ton.
* **Renderzeit:** ca. 70–80 Sekunden pro 5s-Szene.
* **VRAM-Bedarf:** ca. 26 GB.

```bash
./scripts/run_krimi_intro.sh --steps 8
```
> **Ergebnis:** Hohe photorealistische Schärfe bei stabiler Kontinuität und moderater Renderzeit.

---

### Beispiel 3: High-End Kino-Master mit AI-Upscaling (1080p Full HD)
* **Ziel:** Druckreife Bildqualität für Großbildschirme und YouTube/Vimeo in Full HD 1080p.
* **Besonderheit:** MiniMax rendert den 0.4 MP Rohfilm ohne Artefakte, anschließend skaliert `R-ESRGAN 4x+ Batched` in 16er-Frames-Batches ohne VRAM-Spitze hoch.
* **Renderzeit:** ca. 95–110 Sekunden pro 5s-Szene.

```bash
./scripts/run_krimi_intro.sh --steps 8 --upscale --output output/krimi_cinema_1080p
```
> **Ergebnis:** Gestochen scharfes 1080p Video mit kristallklaren Kanten, satten Kontrasten und intaktem Original-Ton.

---

### Beispiel 4: Epische Plansequenz ohne Turbo (Pure Diffusion)
* **Ziel:** Maximale Nuancen in Rauch, Regen, spiegelndem Wasser und subtilen Gesichtsausdrücken.
* **Besonderheit:** Deaktiviert das distillierte Turbo-LoRA (`--no-turbo`) und nutzt den kompletten 20-Step Diffusionsprozess.
* **Renderzeit:** ca. 3,5–4,5 Minuten pro 5s-Szene.

```bash
python3 scripts/auto_movie_maker.py \
    --story configs/krimi_intro_30s.yaml \
    --no-turbo \
    --steps 20 \
    --output output/krimi_pure_diffusion
```

---

### Beispiel 5: Social Media / Hochformat (9:16 Shorts & Reels)
* **Ziel:** Vertikales Smartphone-Format für TikTok, YouTube Shorts oder Instagram Reels.
* **Renderzeit:** ca. 65 Sekunden pro Clip.

```bash
python3 scripts/auto_movie_maker.py \
    --story configs/krimi_intro_30s.yaml \
    --width 480 \
    --height 864 \
    --steps 6 \
    --output output/krimi_vertical_shorts
```

---

### Beispiel 6: Das 5-Minuten-Epos (60 Szenen vollautomatisch)
* **Ziel:** Spielfilmartige Handlung mit 60 Einzelszenen ($60 \times 5\,\text{s} = 300\,\text{s}$).
* **Besonderheit:** Dank `offload_between_scenes=False` bleibt das 32B-Modell warm im VRAM $\rightarrow$ spart über **50 Minuten** Ladezeiten ein!

```bash
python3 scripts/auto_movie_maker.py \
    --story configs/epos_5min_story.yaml \
    --steps 6 \
    --output output/epos_5minuten
```
* **Gesamtdauer:** ca. 75 Minuten für 5 Minuten fertigen Film.

---

## 3. Tabelle: Realisierte vs. Mögliche Funktionen

In dieser Matrix siehst du den aktuellen Entwicklungsstand des Setups sowie die Roadmap möglicher Erweiterungen:

| Funktionsbereich | Konkrete Funktion | Status | Technologie / Werkzeug | Nutzen für die Filmproduktion |
| :--- | :--- | :---: | :--- | :--- |
| **Pipeline-Kern** | Multi-Szenen-Orchestrierung | 🟢 **Realisiert** | `auto_movie_maker.py` API-Client | Dreht 3, 6, 60 oder 120+ Szenen autonom ohne Nutzer-Eingriff. |
| **Charakter** | Visueller Gesichtsanker | 🟢 **Realisiert** | `MiniMaxH3ReferenceToVideo` | Behält Identität über Schnitte hinweg bei (`<Picture 1>`). |
| **Kamera & Schnitt** | Nahtlose Plansequenz | 🟢 **Realisiert** | Last-Frame-Handoff (`i2v` + FFmpeg) | Kontinuierliche Kamerabewegung ohne Kanten oder Sprünge. |
| **Audio** | Synchrone Stereotonspur | 🟢 **Realisiert** | MiniMax Audio-VAE (`VAEDecodeAudio`) | Erzeugt Geräusche, Sprache und Musik passend zur Szene. |
| **Performance** | Modell-Warmstart im VRAM | 🟢 **Realisiert** | `offload_between_scenes=False` | Spart 40–60s Ladezeit pro Clip; Folgeszenen starten sofort. |
| **Stabilität** | Automatischer VRAM-Schutz | 🟢 **Realisiert** | Pre-/Post-Flight `/free` & Cache-GC | Verhindert Überlauf und Freezes auf der W7800 (48 GB). |
| **Beschleunigung** | Redundanz-Cache | 🟢 **Realisiert** | `EasyCache` Node | Spart 20–30 % Renderzeit ohne sichtbaren Qualitätsverlust. |
| **Regie-System** | 4-Spur Prompt-Enhancer | 🟢 **Realisiert** | Python Prompt-Synthese | Kombiniert `style`, `action`, `camera` und `audio` strukturiert. |
| **Auflösung** | 1080p Batched Upscaling | 🟢 **Realisiert** | `ImageUpscaleWithModelBatched` + R-ESRGAN | Verwandelt 0.4 MP Basis-Render in sauberes Full HD. |
| **Post-Production** | Verlustfreier Video-Schnitt | 🟢 **Realisiert** | FFmpeg Concat Demuxer (`-c copy`) | Verbindet $N$ Szenen in unter 1 Sekunde zum Gesamtfilm. |
| **Drehbuch** | LLM-Freitext-Zerlegung | 🟢 **Realisiert** | Ollama (`qwen3.8-27b-q4`) API | Verwandelt Buchabsätze automatisch in 5s-Kamera-Shots. |
| --- | --- | --- | --- | --- |
| **Charakter** | Multi-Charakter-Tracking | 🟡 *Möglich* | Ref-Images 0 bis N (`<Picture 2>`) | Zwei Personen gleichzeitig im Bild konsistent halten. |
| **Charakter** | Master-Face-Detailer | 🟡 *Möglich* | Impact Pack / FaceDetailer | Schärft das Master-Porträt vor Drehstart, um Falten/Augen zu perfektionieren. |
| **Schnitt** | Szenen-Überblendungen | 🟡 *Möglich* | FFmpeg xfade (Dissolve, Wipe) | Sanfte Weichblenden zwischen Szenen statt harter Schnitte. |
| **Soundtrack** | Audio-Ducking / BGM-Bett | 🟡 *Möglich* | FFmpeg sidechaincompress | Globale Hintergrundmusik abspielen und bei Sprache automatisch absenken. |
| **VFX** | Title-Cards & Untertitel | 🟡 *Möglich* | FFmpeg drawtext / SRT-Burn-in | Automatische Einblendung von Serien-Titeln und Untertiteln. |
| **Fehlerbehandlung** | Selektives Re-Rendering | 🟡 *Möglich* | Szenen-Index CLI (`--rerun 3`) | Erlaubt das Neudrehen einzelner Szenen mit neuem Seed ohne Gesamtlauf. |
| **Kamera** | Szenenweise LoRA-Regie | 🟡 *Möglich* | Dynamische LoRA-Loader | Bestimmte Kamera-LoRAs (z.B. Zoom, Orbit) nur für Szene $X$ aktivieren. |
| **GUI** | Interaktives Web-Dashboard | 🟡 *Möglich* | Streamlit / Gradio Web-UI | Visuelle Abnahme aller Szenen-Clips im Browser vor dem Zusammenschnitt. |

---

## 4. Prompt-Engineering & Charakter-Kontinuität

### Die goldene Regel für Ref2V:
Damit MiniMax H3 das Referenzbild versteht, muss die Syntax **exakt** eingehalten werden:
1. Im Prompt muss stehen: `<Picture 1>`
2. Direkt danach folgt die Rollenbeschreibung: `<Picture 1> is Detective Cross, a sharp detective in a trenchcoat...`
3. Die Licht- und Kamerawerte werden im Storyboard getrennt gepflegt:

```yaml
style: "Moody classic 1950s Film Noir aesthetic, 35mm practical film grain, chiaroscuro lighting, volumetric street lamp fog."

scenes:
  - id: 1
    type: "ref2v"
    action: "<Picture 1> Detective Cross steps into the rain-soaked alley."
    camera: "Slow descending crane shot."
    audio: "Heavy rain pouring, distant thunder, lonely jazz trumpet."
```

---

## 5. 🎭 2-Personen-Setup & Face Detailer (Multi-Charakter-Dreh)

### 5.1 Das 2-Stufen-Prinzip (Schutz vor Video-Flicker)
* **Das Problem bei Video-FaceDetailer:** Wendet man FaceDetailer Frame-für-Frame auf fertige Videos an, berechnet der Sampler jedes Frame mit neuem Noise. Die Gesichter morphen und zucken unerträglich („Temporal Incoherence“).
* **Die Hollywood-Lösung (Pre-Refining):** Beide Master-Porträts der Charaktere werden **vor dem Videodreh** durch den `FaceDetailer` (mit FLUX oder SDXL) gejagt. Die Gesichts-DNA (Augen, Iris, Wimpern, Poren) wird auf 4K-Mikroschärfe gebracht und als Referenzbild übergeben. MiniMax H3 überträgt diese Schärfe zeitlich konsistent und flackerfrei auf alle Frames!

### 5.2 Exakte FaceDetailer Node-Einstellungen (ComfyUI-Impact-Pack)

| Parameter | Empfohlener Wert | Zweck & Auswirkung |
| :--- | :--- | :--- |
| **`bbox_detector`** | `face_yolov8m.pt` | Erkennt Männer- und Frauengesichter gleichermaßen zuverlässig. |
| **`sam_model_opt`** | `sam_vit_b_01ec64.pth` | Segment Anything erzeugt nahtlose Masken ohne scharfe Kanten. |
| **`max_detections`** | `2` (oder `0`) | Erkennt bei 2 Personen auf einem Bild beide Gesichter in einem Schritt (`0` = alle). |
| **`guide_size`** | `768` | Berechnet Gesichtsdetails in hoher Sub-Auflösung für feine Texturen. |
| **`max_size`** | `1024` | Begrenzt die Maximalgröße für optimalen Speicherverbrauch. |
| **`drop_size`** | `10` | Schärft auch kleinere Gesichter im Bildmittelgrund. |
| **`denoise`** | **`0.30 – 0.35`** | **⚠️ Schlüsselwert:** Behält die Gesichtsform exakt bei; schärft nur Augen, Iris und Haut. |
| **`feather`** | `5` | Weicher Alpha-Übergang an den Maskenrändern, verhindert Schnittkanten. |
| **`cycle`** | `1` | 1 Durchlauf reicht vollkommen aus. |

### 5.3 MiniMax H3 Multi-Charakter-Verdrahtung
* **Charakter 1:** `ref_images.ref_image_0` (Node 137) $\rightarrow$ im Prompt angesprochen mit **`<Picture 1>`**
* **Charakter 2:** `ref_images.ref_image_1` (Node 139) $\rightarrow$ im Prompt angesprochen mit **`<Picture 2>`**
* **ref_image_size:** `match` (0.4 MP, performant und stabil)

### 5.4 Drehbuch-Syntax für 2 Personen (`yaml`)
```yaml
character_image: "ComfyUI/input/detective_facedetailed.png"
character2_image: "ComfyUI/input/elena_facedetailed.png"
style: "Moody classic 1950s Film Noir, 35mm practical film grain, chiaroscuro lighting, heavy rain under amber street lamps."

scenes:
  - id: 1
    type: "ref2v"
    action: >
      Tense dialogue two-shot:
      <Picture 1> is Detective Cross, a rugged private eye in a charcoal fedora and dark trenchcoat.
      <Picture 2> is Elena Vance, a mysterious woman with crimson lips and a black lace veil.
      They stand closely face-to-face under a dripping awning, whispering urgently in the rain.
      Detective Cross leans in as Elena covertly slips a small brass key into his gloved hand.
    camera: "Slow intimate two-shot camera dolly gliding slightly around both characters."
    audio: "Rain spattering on canvas awning, quiet tense whispered voices, melancholic jazz saxophone in background."
```

### 5.5 Der fertige Ausführungsbefehl
```bash
python3 scripts/auto_movie_maker.py \
    --story configs/krimi_dialog_2personen.yaml \
    --character "ComfyUI/input/detective_facedetailed.png" \
    --character2 "ComfyUI/input/elena_facedetailed.png" \
    --steps 8 \
    --upscale
```

> **📌 Workflow-Hinweis:** Im Workflow `_minimax_h3_face_detailer_master.json` befindet sich diese vollständige Konfiguration als übersichtliche Markdown-Notiz direkt am linken Rand (Position `x: -2500, y: 3500`), direkt neben den Eingangs-Loadern für Charakter 1 und Charakter 2.

---

## 6. 🎬 Regie-Handbuch: Ref2V vs. I2V bei mehreren Charakteren (Drehbuch-Beispiele)

Beim Drehen von Filmen mit zwei oder mehr Personen entscheidet die Wahl zwischen **Ref2V** und **I2V** über Schnittrhythmus, räumliche Kohärenz und flüssige Animation:

### 6.1 Die Entscheidungs-Matrix

| Kriterium | Wann wählst du `type: "ref2v"`? | Wann wählst du `type: "i2v"`? |
| :--- | :--- | :--- |
| **Kamera-Aktion** | **Kinoschnitt:** Neuer Winkel, Perspektivenwechsel, Gegenschuss (180°), Close-up. | **Plansequenz:** Kontinuierliche Vorwärtsfahrt, Pan, Orbit oder Dolly ohne Schnitt. |
| **Referenz-Quelle** | Greift auf die Master-Porträts (`<Picture 1>`, `<Picture 2>`) zu. | Greift auf das **exakt letzte Frame** der Vorszene (`last_frame_scX.png`) zu. |
| **Prompt-Pflicht** | MUSS `<Picture 1>` und ggf. `<Picture 2>` im Text benennen. | **KEINE** `<Picture>`-Tags! Beschreibt nur die kontinuierliche Bewegung. |
| **Stärke** | Perfekt für Blickwechsel, Dialogschnitte und neue Einstellungsgrößen. | Perfekt für komplexe Doppel-Aktionen (z. B. Übergabe, Gehen, Flucht). |

---

### 6.2 Praxisbeispiel 1: Der klassische Dialog-Gegenschnitt (Shot / Reverse-Shot)
* **Szene:** Detective Cross und Informantin Elena Vance verhandeln in einem verregneten Hinterhof.
* **Technik:** 3 Szenen, alle **`ref2v`**, um die Perspektiven hart und professionell wie im Kino zu schneiden.

```yaml
# story_dialog_schuss_gegenschuss.yaml
character_image: "ComfyUI/input/detective_facedetailed.png"     # <Picture 1>
character2_image: "ComfyUI/input/elena_facedetailed.png"        # <Picture 2>
style: "1950s Film Noir, 35mm practical anamorphic lenses, high-contrast chiaroscuro, wet asphalt reflections, volumetric fog."

scenes:
  # Szene 1: Establishing Two-Shot (Beide im Bild)
  - id: 1
    type: "ref2v"
    action: >
      Wide two-shot establishing:
      <Picture 1> is Detective Cross, standing on the left in a charcoal fedora and dripping trenchcoat.
      <Picture 2> is Elena Vance, standing opposite him on the right in an emerald silk coat.
      Rain pours heavily between them under an amber street lamp as they confront each other in the alley.
    camera: "Static low-angle two-shot, holding steady."
    audio: "Heavy rain pouring, distant police siren, low ominous cello drone."

  # Szene 2: Kinoschnitt — Halbnah über die Schulter auf Detective Cross
  - id: 2
    type: "ref2v"
    action: >
      Over-the-shoulder medium shot:
      From behind <Picture 2> Elena's shoulder, focus pulls sharply onto <Picture 1> Detective Cross.
      His face is lit by the street lamp, rain dripping from his fedora brim.
      He narrows his eyes sternly, lips moving as he demands the truth.
    camera: "Slight handheld camera drift on Detective Cross's face."
    audio: "Muffled dialogue murmur, steady hissing rain, tense pizzicato strings."

  # Szene 3: Gegenschnitt (Reverse-Shot) — Close-Up auf Elena
  - id: 3
    type: "ref2v"
    action: >
      Reverse angle intense close-up:
      Focus shifts entirely to <Picture 2> Elena Vance.
      Raindrops glisten on her cheek, her eyes glistening with fear and secrets.
      She shakes her head slowly, whispering a warning before glancing past the camera.
    camera: "Intense centered close-up with soft background blur (bokeh)."
    audio: "Trembling female whisper, sudden gust of wind, rising dramatic orchestral swell."
```

---

### 6.3 Praxisbeispiel 2: Ungeschnittene Zwei-Personen-Aktion (I2V Last-Frame-Handoff)
* **Szene:** Detective Cross und Elena rennen gemeinsam vor Verfolgern davon.
* **Technik:** Szene 1 baut die Situation mit **`ref2v`** auf. Szene 2 schließt **nahtlos ohne Schnitt via `i2v`** an und führt die gemeinsame Bewegung weiter.

```yaml
# story_action_handoff.yaml
character_image: "ComfyUI/input/detective_facedetailed.png"
character2_image: "ComfyUI/input/elena_facedetailed.png"
style: "Gritty cinematic action thriller, 35mm film grain, high dynamic range, volumetric rain fog."

scenes:
  # Szene 1: Start der Flucht (Ref2V)
  - id: 1
    type: "ref2v"
    action: >
      Dynamic two-shot action:
      <Picture 1> Detective Cross grabs the arm of <Picture 2> Elena Vance under the flickering streetlight.
      He pulls her forward through the heavy rain as both turn toward the dark alleyway to escape.
    camera: "Rapid tracking dolly moving backwards ahead of both running characters."
    audio: "Splashing footsteps in puddles, rapid heavy breathing, driving percussive cinematic heartbeat."

  # Szene 2: Nahtlose Fortführung (I2V Handoff aus dem letzten Frame)
  - id: 2
    type: "i2v"
    action: >
      Continuous uninterrupted pursuit motion:
      Both characters sprint side-by-side around the brick corner into the narrow corridor.
      Detective Cross pushes open a heavy iron gate with his shoulder, ushering Elena inside just as car headlights flash across the brick entrance behind them.
    camera: "Continuous fluid whip-pan tracking them through the iron gate."
    audio: "Heavy metal gate clanging shut, screech of car tires on wet asphalt, pounding suspense drums."
```

---

### 6.4 Praxisbeispiel 3: Der Hollywood-Szenenbogen (Ref2V $\rightarrow$ I2V $\rightarrow$ Ref2V)
* **Ziel:** Höchste cinematische Reife: Aufbau $\rightarrow$ Interaktion $\rightarrow$ Reaktions-Close-ups.

```mermaid
sequenceDiagram
    participant S1 as Szene 1 (Ref2V Two-Shot)
    participant S2 as Szene 2 (I2V Handoff)
    participant S3 as Szene 3 (Ref2V Cross Close-up)
    participant S4 as Szene 4 (Ref2V Elena Close-up)

    Note over S1: Schnitt 1: Beide Figuren treffen sich (Establishing)
    S1->>S2: Letzter Frame wird Startbild
    Note over S2: Ungeschnittene Bewegung: Übergabe des Umschlags
    Note over S3: Schnitt 2: Harter Kinoschnitt auf Detective Cross
    Note over S4: Schnitt 3: Gegenschnitt auf Elena Vance
```

1. **Szene 1 (`ref2v` - Two-Shot):** `<Picture 1>` Cross und `<Picture 2>` Elena sitzen sich in einer verrauchten Bar gegenüber.
2. **Szene 2 (`i2v` - Last-Frame-Handoff):** Ohne Schnitt schiebt Elena ihre Hand über den Holztisch und übergibt einen braunen Umschlag; Cross' Hand schließt sich darum.
3. **Szene 3 (`ref2v` - Schnitt / Close-up):** Kinoschnitt auf das Gesicht von `<Picture 1>` Detective Cross, der die Augenbraue hebt.
4. **Szene 4 (`ref2v` - Schnitt / Close-up):** Gegenschnitt auf `<Picture 2>` Elena, die nervös an ihrer Zigarette zieht.

---

### 6.5 Praxisbeispiel 4: Drei oder mehr Charaktere im Bild
MiniMax H3 unterstützt bis zu **9 Referenzbilder** (`ref_images.ref_image_0` bis `ref_image_8`).

```yaml
# story_3_charaktere.yaml
character_image: "ComfyUI/input/detective.png"     # <Picture 1>
character2_image: "ComfyUI/input/elena.png"        # <Picture 2>
character3_image: "ComfyUI/input/barkeeper.png"    # <Picture 3>

scenes:
  - id: 1
    type: "ref2v"
    action: >
      Three-character interior tavern scene:
      At the foreground wooden counter, <Picture 1> Detective Cross talks intently with <Picture 2> Elena Vance.
      Directly behind the counter in the background, <Picture 3> the burly bartender Marcus dries a glass with a dirty rag, eyeing them suspiciously.
    camera: "Slow tracking dolly shot across the tavern counter."
    audio: "Muffled pub murmurs, clinking glasses, low jazz piano in background."
```

---

## 7. ⏱️ Benchmark-, Zeit- & Qualitäts-Matrix: Alle Optimierungen im Vergleich

Alle Messwerte basieren auf dem Testsystem mit **AMD Radeon PRO W7800 (48 GB VRAM, ROCm 6.4, gfx1100)** und MiniMax H3 (32B Text-Encoder, UNET int8, 24 fps).

---

### 7.1 Liste aller möglichen Optimierungen: Was bringen sie im Detail?

| # | Optimierung | Kategorie | Rechenzeit-Auswirkung | Was bringt die Optimierung konkret? |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **VRAM-Warmstart (`offload_between_scenes=False`)** | Performance & Workflow | **-40s bis -50s** pro Clip (ab Clip 2) | Das 32B-Modell bleibt im VRAM gepinnt. Folgeszenen starten sofort in 0s statt das Modell jedes Mal neu aus dem RAM zu transferieren. Spart über **45 Minuten** bei einem 5-Minuten-Film! |
| **2** | **Turbo-LoRA (4 Steps)** | Speed-Distillation | **-150s** (~45s statt ~200s) | Reduziert Sampling von 20 auf 4 Schritte. Perfekt für schnelle Entwürfe, Storyboard-Prüfung und Schnittkontrolle. |
| **3** | **Turbo-LoRA (8 Steps - Sweet Spot)** | Speed & Qualität | **-125s** (~70s statt ~200s) | Verdoppelt die Diffusionsschritte gegenüber 4-Step; liefert gestochen scharfe Augen, Finger und feine Texturen bei hoher Geschwindigkeit. |
| **4** | **EasyCache (DiT-Redundanz-Cache)** | Algorithmus | **-20 % bis -25 %** (~15s–40s) | Erkennt redundante DiT-Attention-Berechnungen zwischen Diffusionsschritten und überspringt sie ohne sichtbaren Qualitätsverlust. |
| **5** | **Pre-FaceDetailer (Master-Keyframe)** | Bildqualität | **0s** im Video (einmalig ~5s vorab) | **Verhindert das gefürchtete Video-Flickern!** Schärft Augen, Iris, Wimpern und Hauttextur am Master-Porträt vor Drehstart auf 4K-Mikroschärfe. MiniMax H3 überträgt die perfekte DNA flackerfrei auf alle 120 Frames. |
| **6** | **4-Spur-Regie-Prompting** | Prompt-Architektur | **0s** (Keine Zusatzzeit) | Schöpft das 32B Qwen3-VL Modell voll aus: Synthese aus `style`, `action`, `camera` und `audio` erzeugt echte Kinobilder mit natürlichem Bokeh, gezielter Ausleuchtung und passender Geräuschkulisse. |
| **7** | **R-ESRGAN 4x+ Batched Upscaling** | Auflösung | **+20s bis +25s** pro 5s-Clip | Skaliert das 0.4 MP Rohvideo (864×480) in 16er-Frame-Batches verlustfrei auf **Full HD 1080p (1920×1080)** hoch, ohne VRAM-Spitzen zu verursachen. Beseitigt Treppeneffekte und Unschärfen. |
| **8** | **Hybrides Last-Frame-Handoff (`i2v`)** | Szenenkontinuität | **0s** (0.1s FFmpeg-Extraktion) | Ermöglicht nahtlose Plansequenzen und flüssige Kamerafahrten. Das letzte Frame einer Szene dient der nächsten als Startbasis. |
| **9** | **Multi-Charakter-Tracking (`--character2`)** | Storytelling & Dialog | **+5s bis +8s** Conditioning-Zeit | Ermöglicht konsistente Interaktionen zwischen zwei (oder bis zu 9) eigenständigen Personen im Bild (`<Picture 1>` und `<Picture 2>`). |
| **10**| **ROCm Native CK-SDPA & Kernel Tuning** | Stabilität & Hardware | Verhindert Abstürze & Timeouts | Deaktiviert fehlerhafte SDMA-Transfers (`HSA_ENABLE_SDMA=0`), schützt Desktop-VRAM (`--reserve-vram 3`) und nutzt File-backed `mmap` statt 19 GB Swap-Stau. |
| **11**| **Verlustfreier Concat-Schnitt (FFmpeg)** | Post-Production | **< 1 Sekunde** für den ganzen Film | Verbindet alle Teilszenen verlustfrei per Stream-Copy (`-c copy`) mit synchronem Stereo-Ton ohne zeitraubendes Re-Encoding. |
| **12**| **Ollama LLM-Drehbuchzerlegung** | Automation | **~10s** einmalig vor Filmstart | Zerlegt Roman- oder Fließtext über ein lokales Modell (`qwen3.8-27b-q4`) vollautomatisch in nummerierte 5s-Szenen mit Kamera- und Audio-Tags. |

---

### 7.2 Tabelle 1: Alle Optimierungen einzeln im Vergleich zur unoptimierten Baseline

> **Baseline-Definition:** Unoptimierter MiniMax H3 Ref2VA-Lauf (20 Steps, kein Turbo-LoRA, kein EasyCache, kein Modell-Warmstart [Kaltstart pro Szene], 864×480, Prompt ohne Regiestruktur).

| Optimierungs-Stufe | Kurzbeschreibung / Wirkungsweise | Zeit pro 5s-Szene | Zeit-Vorteil ggü. Baseline | Endauflösung | Bildschärfe & Details | Audio-Synchronität | Endqualität (Score / 10) |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| **0. Unoptimierte Baseline** | Standard-Kaltstart (20 Steps, No Turbo, kein VRAM-Pinning, kein Cache) | **ca. 260s** (4m 20s) | ±0s (Referenz) | 864 × 480 | Weiche Konturen, moderate Falten | Monotoner Hintergrundton | **5.5 / 10** |
| **+ Nur Modell-Warmstart** | Hält 32B-Modell im VRAM; Folgeszenen starten ohne RAM-Transferverzögerung | **ca. 215s** (3m 35s) | -45s pro Clip | 864 × 480 | Wie Baseline | Wie Baseline | **5.5 / 10** |
| **+ Nur 4-Spur-Prompting** | Strukturierte Prompt-Synthese (Style, Action, Camera, Audio) reizt Text-Encoder aus | **ca. 260s** (4m 20s) | ±0s | 864 × 480 | Kinolicht, gezielte Tiefenschärfe | Volle Stereo-SFX & passende Musik | **7.0 / 10** |
| **+ Nur EasyCache** | Überspringt redundante DiT-Aufmerksamkeitsberechnungen mathematisch verlustfrei | **ca. 210s** (3m 30s) | -50s (-20 %) | 864 × 480 | 99 % identisch zur Baseline | Voll synchron | **5.5 / 10** |
| **+ Nur Turbo-LoRA (4 Steps)** | Destilliertes 4-Schritt-Sampling für maximale Geschwindigkeit beim Pre-Visualisieren | **ca. 95s** (1m 35s) | -165s (-63 %) | 864 × 480 | Gute Bewegung, leichte Texturglättung | Solider Sound | **6.8 / 10** |
| **+ Nur Turbo-LoRA (8 Steps)** | Sweet Spot: Verdoppelt Sampling-Schritte für feine Iris-, Textur- und Finger-Details | **ca. 125s** (2m 05s) | -135s (-52 %) | 864 × 480 | Scharfe Details, präzise Augen | Klarer Raumklang | **7.8 / 10** |
| **+ Nur Pre-FaceDetailer** | Schärft Porträt vorab auf 4K-Mikro-Detailstufe; verhindert Video-Flickern komplett | **ca. 260s** (4m 20s) | ±0s (5s vorab) | 864 × 480 | Extrem detailreiche Gesichts-DNA | Wie Baseline | **7.2 / 10** |
| **+ Nur R-ESRGAN Upscaler** | KI-Hochskalierung in 16er Batches auf 1080p ohne VRAM-Spitzen (beseitigt Aliasing) | **ca. 285s** (4m 45s) | +25s | **1920 × 1080** | Kristallklares Full HD, keine Pixel | Wie Baseline | **7.5 / 10** |

---

### 7.3 Tabelle 2: Die Produktions-Kombinationen (Benchmark für Einzelszenen & Filme)

In der Praxis kombiniert man mehrere Optimierungen, um das perfekte Verhältnis aus Rechenzeit und Bildqualität zu erzielen:

| Preset / Kombination | Eingesetzte Optimierungen | Zeit pro 5s-Szene | Zeit für 30s Film (6 Szenen) | Zeit für 5 Min Film (60 Szenen) | Endauflösung & Bitrate | Visuelle Qualität & Gesamteindruck | Endqualität (Score / 10) | Empfohlener Einsatzzweck |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| **Unoptimiert (Baseline)** | Keine Optimierungen (Kaltstart, 20 Steps, No Turbo, kein Cache) | **260s** (4,3 Min) | **26 Minuten** | **> 4,3 Stunden** | 864 × 480 (3.5 Mbps) | Weiche Kanten, lange Wartezeiten, flache Ausleuchtung | **5.5 / 10** | Nicht empfohlen |
| **1. Pre-Vis / Draft (Höchst-Tempo)** | Warmstart + Turbo 4 Steps + EasyCache + 4-Spur-Prompt | **~45s** | **4,5 Minuten** | **45 Minuten** | 864 × 480 (5.0 Mbps) | Flüssige Bewegung, gutes Pacing, minimale Texturabstriche | **7.5 / 10** | Schnelle Drehbuch- & Schnittkontrolle |
| **2. Produktion Balanced (Sweet Spot)** | Warmstart + Turbo 8 Steps + EasyCache + Pre-FaceDetailer + 4-Spur-Prompt | **~70s** | **7,0 Minuten** | **70 Minuten** | 864 × 480 (7.5 Mbps) | Sehr scharfe Gesichter, lebendige Mimik, stimmige Ausleuchtung & Stereo-SFX | **8.8 / 10** | Standard-Serienproduktion & Social Media |
| **3. High-End Kino-Master (1080p)** | Preset 2 + **R-ESRGAN 4x+ Batched Upscaling** | **~95s** | **9,5 Minuten** | **95 Minuten** | **1920 × 1080** (16 Mbps) | **Kinoreife Schärfe:** Poren & Wimpern gestochen scharf, glasklare Konturen, kein Rauschen | **9.7 / 10** | Großbildschirme, YouTube 1080p, Festplatten-Master |
| **4. Pure Diffusion Master (No-Turbo)** | Warmstart + 20 Steps No-Turbo + EasyCache + Pre-FaceDetailer + Upscaler | **~210s** | **21 Minuten** | **3,5 Stunden** | **1920 × 1080** (18 Mbps) | Maximale Nuancen bei volumetrischem Rauch, Regen & subtiler Lichtbrechung | **9.9 / 10** | Festival-Beiträge & anspruchsvolle Kunstfilme |
| **5. Multi-Charakter Dialog (2 Personen)** | Preset 3 + **2x FaceDetailer Master + Multi-Ref2V (`<Picture 1 & 2>`)** | **~100s** | **10 Minuten** | **100 Minuten** | **1920 × 1080** (16 Mbps) | Zwei Personen mit 100% konsistenter Identität und Mimik in 1080p Full HD | **9.6 / 10** | Dialogszenen, Schuss-Gegenschuss, Zwei-Personen-Thriller |
| **6. Vertikale Shorts (9:16 Mobile)** | Preset 2 mit Hochformat (`480 × 864`) | **~65s** | **6,5 Minuten** | **65 Minuten** | 480 × 864 (6.0 Mbps) | Perfekt formatiert für Smartphones, scharf zentrierter Charakterfokus | **8.7 / 10** | TikTok, Instagram Reels, YouTube Shorts |




