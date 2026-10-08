# 🎬 Konkreter Praxisleitfaden: Multi-Stage Workflows & Video-Erweiterung in ComfyUI
## Exakte Klick-für-Klick Anleitung mit den realen ComfyUI-Knoten für MiniMax H3 und Wan 2.2

---

## 📑 Inhaltsverzeichnis
1. [Das Grundproblem & der Reality-Check](#1-das-grundproblem--der-reality-check)
2. [Die 6 realen ComfyUI-Knoten (Genau so heißen sie im Menü)](#2-die-6-realen-comfyui-knoten-genau-so-heißen-sie-im-menü)
3. [Klick-für-Klick: Der 15s-Multi-Stage-Workflow (3 Szenen + Einzelclips)](#3-klick-für-klick-der-15s-multi-stage-workflow-3-szenen--einzelclips)
   - [Schritt 1: Szene 1 aufbauen](#schritt-1-szene-1-aufbauen)
   - [Schritt 2: Das Bindeglied (Letzten Frame aus dem Video ziehen)](#schritt-2-das-bindeglied-letzten-frame-aus-dem-video-ziehen)
   - [Schritt 3: Szene 2 anfügen](#schritt-3-szene-2-anfügen)
   - [Schritt 4: Szene 3 anfügen](#schritt-4-szene-3-anfügen)
   - [Schritt 5: Den 15s-Gesamtfilm zusammenfügen](#schritt-5-den-15s-gesamtfilm-zusammenfügen)
4. [Der vollständige Schaltplan (Mermaid & ASCII)](#4-der-vollständige-schaltplan-mermaid--ascii)
5. [Was nach dem Rendern auf der Festplatte liegt](#5-was-nach-dem-rendern-auf-der-festplatte-liegt)
6. [Bestehendes Video erweitern (Ohne Neurendern!)](#6-bestehendes-video-erweitern-ohne-neurendern)
   - [Weg A: Direkt in ComfyUI mit Load Video](#weg-a-direkt-in-comfyui-mit-load-video)
   - [Weg B: Der 1-Sekunden-Terminal-Weg mit FFmpeg](#weg-b-der-1-sekunden-terminal-weg-mit-ffmpeg)
7. [Goldene Prompting-Regeln für Folgeszenen](#7-goldene-prompting-regeln-für-folgeszenen)

---

> [!TIP]
> **⚡ Fertige Vorlage zum Direkt-Laden:**  
> Wenn du nicht alle 21 Knoten von Hand verkabeln möchtest, habe ich dir die fertige Vorlage direkt in deinen Workflow-Ordner gelegt:  
> `ComfyUI/user/default/workflows/minimax_h3_multistage_maus_15s.json`  
> In ComfyUI einfach oben auf **Workflow ➔ Open** klicken und auswählen. Startbild in `Load Image` reinziehen und *Queue Prompt* drücken!

---

## 1. Das Grundproblem & der Reality-Check

In den Standard-Vorlagen für **MiniMax H3** (`video_minimax_h3_i2v_amd.json`) und **Wan 2.2** (`wan2.2_i2v.json`) siehst du auf deinem Bildschirm **keine** einzelnen Sampler- oder VAE-Knoten. 

Comfy-Org fasst die gesamte KI-Logik (DiT, VLM-Encoder, VAE und KSampler) in einem **einzigen großen Gruppen-Knoten** zusammen:
* Bei MiniMax heißt er: **`Image to Video (MiniMax H3)`**
* Bei Wan 2.2 heißt er: **`Image to Video (Wan2.2)`**

### Das Anschluss-Problem:
* Dieser Block hat als Eingang ein Bild: **`first_frame`** (Typ: `IMAGE`, blaue Buchse).
* Als Ausgang liefert er aber ein fertiges Video: **`VIDEO`** (Typ: `VIDEO`, lila Buchse).
* Du kannst den Ausgang **`VIDEO`** **NICHT** direkt in den Eingang **`first_frame`** des nächsten Blocks stecken, weil ComfyUI ein Video nicht direkt als Bild akzeptiert!

👉 **Hier kommt der entscheidende Zwischenschritt:** Wir müssen das Video in Einzelbilder zerlegen und exakt das **letzte Bild** abgreifen.

---

## 2. Die 6 realen ComfyUI-Knoten (Genau so heißen sie im Menü)

Wenn du im ComfyUI-Canvas die **Leertaste** drückst (oder **Doppelklick** machst), suche nach genau diesen exakten Begriffen:

| Knoten-Name in ComfyUI | Typ | Was er tut |
| :--- | :--- | :--- |
| **`Load Image`** | Eingabe | Lädt dein allererstes Startbild (z. B. Maus im Käseladen). |
| **`Resolution Selector`** | Einstellung | Liefert `width` und `height` an alle Szenen-Blöcke. |
| **`Image to Video (MiniMax H3)`** *(oder Wan2.2)* | KI-Kern | Berechnet 5 Sekunden Video aus Bild + Prompt. Ausgang: `VIDEO`. |
| **`Get Video Components`** | Wandler | Wandelt das Signal `VIDEO` in Einzelbilder (`IMAGE`) und Audio (`AUDIO`) um. |
| **`SelectImages`** | Filter | Wählt mit `indexes: -1` exakt den **letzten Frame** des Videos als neues Startbild aus. |
| **`Save Video`** | Speicher | Schreibt den Clip (oder Gesamtfilm) als MP4 auf die Festplatte. |
| **`Concatenate Video`** | Schnitt | Hängt mehrere `VIDEO`-Signale nahtlos ohne Qualitätsverlust hintereinander. |

---

## 3. Klick-für-Klick: Der 15s-Multi-Stage-Workflow (3 Szenen + Einzelclips)

Öffne deinen Basis-Workflow: `video_minimax_h3_i2v_amd.json` (oder `wan2.2_i2v.json`).

---

### Schritt 1: Szene 1 aufbauen
1. Der Knoten **`Load Image`** enthält dein Ausgangsbild (z. B. `maus_start.png`).
2. Verbinde den Ausgang **`IMAGE`** von `Load Image` mit dem Eingang **`first_frame`** des ersten Blocks **`Image to Video (MiniMax H3)`**.
3. Verbinde `width` und `height` von **`Resolution Selector`** mit den Eingängen `width` und `height` des Blocks.
4. **Prompt für Szene 1** in die Textbox schreiben:
   * *„A small brown mouse in a tweed vest walks cautiously into an old cheese shop, looking around in awe. Cinematic lighting.“*
5. **Einzelclip von Szene 1 speichern:**
   * Leertaste drücken -> tippe **`Save Video`** ein -> Enter.
   * Verbinde den Ausgang **`VIDEO`** von Stufe 1 mit dem Eingang **`video`** dieses neuen `Save Video`-Knotens.
   * Klicke auf das Textfeld `filename_prefix` und ändere es zu: **`video/maus_szene_01`**.

---

### Schritt 2: Das Bindeglied (Letzten Frame aus dem Video ziehen)
Jetzt bereiten wir das Startbild für Szene 2 vor:

1. Leertaste drücken -> tippe **`Get Video Components`** ein -> Enter.
   * Verbinde den Ausgang **`VIDEO`** von Stufe 1 mit dem Eingang **`video`** von `Get Video Components`.
2. Leertaste drücken -> tippe **`SelectImages`** ein -> Enter.
   * Verbinde den Ausgang **`images`** von `Get Video Components` mit dem Eingang **`image`** von `SelectImages`.
   * **Sehr wichtig:** Klicke in `SelectImages` auf das Feld `indexes` und trage dort ein:
     ```text
     -1
     ```
   *(Erklärung: `-1` bedeutet in Python und ComfyUI immer das allerletzte Element – also exakt der letzte Frame des Videos!)*

---

### Schritt 3: Szene 2 anfügen
1. **Block duplizieren:**
   * Klicke den Block **`Image to Video (MiniMax H3)`** von Stufe 1 an.
   * Drücke `Strg + C` und danach `Strg + V`. Du hast jetzt einen identischen zweiten Block (Stufe 2).
2. **Verkabeln:**
   * Verbinde den Ausgang **`IMAGE`** von **`SelectImages`** (aus Schritt 2) mit dem Eingang **`first_frame`** deines neuen Blocks (Stufe 2)!
   * Verbinde `width` und `height` vom `Resolution Selector` auch mit diesem zweiten Block.
3. **Prompt für Szene 2:**
   * Lösche den alten Text im Prompt-Feld von Stufe 2 und schreibe die Folgehandlung:
   * *„The mouse reaches the counter, pulls a shiny gold coin from its pouch, and places it on the wood surface, pointing at the cheese wedge.“*
4. **Einzelclip von Szene 2 speichern:**
   * Erstelle einen weiteren Knoten **`Save Video`**.
   * Verbinde den Ausgang **`VIDEO`** von Stufe 2 mit diesem `Save Video`.
   * Setze `filename_prefix` auf: **`video/maus_szene_02`**.

---

### Schritt 4: Szene 3 anfügen
Wiederhole das Prinzip für die dritte Stufe:

1. Erstelle ein zweites Paar aus **`Get Video Components`** und **`SelectImages (indexes: -1)`**.
2. Verbinde den Ausgang **`VIDEO`** von Stufe 2 mit dem neuen `Get Video Components`.
3. Ausgang `images` an `SelectImages`.
4. Dupliziere den MiniMax-Block ein drittes Mal (`Strg + C`, `Strg + V` für Stufe 3).
5. Verbinde den Ausgang von `SelectImages` mit **`first_frame`** von Stufe 3.
6. **Prompt für Szene 3:**
   * *„The mouse grabs the wrapped cheese wedge with both paws, hugs it proudly, and scampers out the shop door with a joyful expression.“*
7. **Einzelclip von Szene 3 speichern:**
   * Weiterer `Save Video`-Knoten an Ausgang `VIDEO` von Stufe 3.
   * `filename_prefix`: **`video/maus_szene_03`**.

---

### Schritt 5: Den 15s-Gesamtfilm zusammenfügen
Damit du alle drei Szenen am Ende als ein einziges, durchgehendes 15-Sekunden-Video erhältst:

1. Leertaste drücken -> tippe **`Concatenate Video`** ein -> Enter.
2. Dieser Knoten hat einen erweiterbaren Video-Eingang:
   * Ziehe den Ausgang **`VIDEO`** von Stufe 1 auf den Eingang `video` (wird zu `video_1`).
   * Ziehe den Ausgang **`VIDEO`** von Stufe 2 auf den neu erscheinenden Slot `video_2`.
   * Ziehe den Ausgang **`VIDEO`** von Stufe 3 auf den Slot `video_3`.
3. Erstelle einen vierten **`Save Video`**-Knoten:
   * Verbinde den Ausgang von `Concatenate Video` mit diesem `Save Video`.
   * Setze `filename_prefix` auf: **`video/maus_komplett_15s`**.

---

## 4. Der vollständige Schaltplan (Mermaid & ASCII)

Hier ist die exakte Schaltung im Überblick:

```mermaid
flowchart TD
    subgraph Input["🎬 START"]
        IMG["Load Image\n(maus_start.png)"]
        RES["Resolution Selector\n(z.B. 1344 x 768)"]
    end

    subgraph Szene1["1. SZENE 1 (0s - 5s)"]
        IMG -->|IMAGE| MM1["Image to Video (MiniMax H3)\nPrompt: Maus betritt Laden"]
        RES -.->|width / height| MM1
        MM1 -->|VIDEO| SV1["💾 Save Video\n'video/maus_szene_01'"]
        MM1 -->|VIDEO| GVC1["Get Video Components"]
        GVC1 -->|images| SI1["SelectImages\nindexes: -1"]
    end

    subgraph Szene2["2. SZENE 2 (5s - 10s)"]
        SI1 -->|IMAGE (Letzter Frame)| MM2["Image to Video (MiniMax H3)\nPrompt: Maus bezahlt mit Münze"]
        RES -.->|width / height| MM2
        MM2 -->|VIDEO| SV2["💾 Save Video\n'video/maus_szene_02'"]
        MM2 -->|VIDEO| GVC2["Get Video Components"]
        GVC2 -->|images| SI2["SelectImages\nindexes: -1"]
    end

    subgraph Szene3["3. SZENE 3 (10s - 15s)"]
        SI2 -->|IMAGE (Letzter Frame)| MM3["Image to Video (MiniMax H3)\nPrompt: Maus verlässt Laden mit Käse"]
        RES -.->|width / height| MM3
        MM3 -->|VIDEO| SV3["💾 Save Video\n'video/maus_szene_03'"]
    end

    subgraph Master["🏆 GESAMTFILM (15s)"]
        MM1 -->|video_1| CONCAT["Concatenate Video"]
        MM2 -->|video_2| CONCAT
        MM3 -->|video_3| CONCAT
        CONCAT -->|VIDEO| SVMaster["💾 Save Video\n'video/maus_komplett_15s'"]
    end
```

---

## 5. Was nach dem Rendern auf der Festplatte liegt

Klicke auf **Queue Prompt**. ComfyUI rechnet nun der Reihe nach Szene 1, 2 und 3 durch.

In deinem Verzeichnis `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/output/video/` liegen anschließend automatisch **4 fertige MP4-Dateien**:

1. 📄 `maus_szene_01_00001_.mp4` *(5 Sekunden: Betreten des Ladens)*
2. 📄 `maus_szene_02_00001_.mp4` *(5 Sekunden: Bezahlung am Tresen)*
3. 📄 `maus_szene_03_00001_.mp4` *(5 Sekunden: Stolzer Abgang mit Käse)*
4. 🏆 `maus_komplett_15s_00001_.mp4` *(15 Sekunden: Der fertige, nahtlose Kurzfilm!)*

> [!TIP]
> **Der große Vorteil:** Du hast den fertigen Film sofort fertig geschnitten, behältst aber alle Rohschnitte verlustfrei griffbereit für eventuelle Farbkorrekturen oder Toneffekte in DaVinci Resolve oder CapCut.

---

## 6. Bestehendes Video erweitern (Ohne Neurendern!)

Häufiges Szenario: Du hast gestern ein 15-Sekunden-Video (`film_15s.mp4`) gerendert. Es ist perfekt, und du möchtest **weitere 5 Sekunden anhängen**, **ohne die ersten 15 Sekunden neu zu berechnen!**

Hierfür gibt es zwei extrem einfache Wege:

### Weg A: Direkt in ComfyUI mit `Load Video`

1. Öffne deinen Image-to-Video Workflow.
2. Leertaste drücken -> tippe **`Load Video`** (oder `Load Video (Upload)`) ein.
3. Klicke auf *choose file to upload* und wähle dein fertiges Video `film_15s.mp4`.
4. Hänge an den Ausgang von `Load Video`:
   * Wenn der Ausgang `VIDEO` ist: `Get Video Components` -> `SelectImages (indexes: -1)`.
   * Wenn der Ausgang direkt `IMAGE` ist (z. B. aus Video Helper Suite): direkt `SelectImages (indexes: -1)`.
5. Verbinde den Bildausgang von `SelectImages` mit **`first_frame`** deines MiniMax- oder Wan-Blocks.
6. Schreibe den Prompt für die Verlängerung (Szene 4) und klicke auf **Queue Prompt**.
7. Es werden **nur die neuen 5 Sekunden gerechnet** (Dauer: ca. **85 Sekunden**).
8. Im `Save Video`-Knoten speicherst du den neuen Clip als `video/maus_szene_04`.

---

### Weg B: Der 1-Sekunden-Terminal-Weg mit FFmpeg (Profi-Methode)

Wenn du ComfyUI schlank halten willst, machst du die Frame-Extraktion und das Zusammenfügen im Terminal:

#### 1. Den exakt letzten Frame aus dem 15s-Video ziehen (Dauer: 0,1s):
```bash
cd /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/output/video

ffmpeg -sseof -0.1 -i maus_komplett_15s_00001_.mp4 -update 1 -q:v 1 start_szene4.png
```
* Das Bild `start_szene4.png` liegt nun in deinem Ordner.
* Ziehe es in ComfyUI einfach in den Standard-Knoten **`Load Image`**.
* Rendere Szene 4 (ergibt `maus_szene_04_00001_.mp4`).

#### 2. Beide Videos in 1 Sekunde verlustfrei aneinanderhängen:
```bash
cat << 'EOF' > film_liste.txt
file 'maus_komplett_15s_00001_.mp4'
file 'maus_szene_04_00001_.mp4'
EOF

ffmpeg -f concat -safe 0 -i film_liste.txt -c copy maus_20s_erweitert.mp4
```
* **Ergebnis:** Du hast dein 20-Sekunden-Video in **1 Sekunde** zusammengefügt, ohne Re-Encoding und ohne Qualitätsverlust!

---

## 7. Goldene Prompting-Regeln für Folgeszenen

Wenn du Folgeszenen über den letzten Frame ansteuerst:

* ❌ **Falsch:** Die Figur und Kleidung von Grund auf neu beschreiben:  
  *„A tiny brown mouse with fluffy fur, wearing a tweed vest and leather backpack...“*  
  *(Das verwirrt das Modell, da es das Aussehen bereits aus dem Bild kennt. Wiederholte Beschreibungen führen oft zu leichten Halluzinationen oder Kostümwechseln!)*
* ✔️ **Richtig:** Beschreibe **nur die neue Handlung, Bewegung und Kamerafahrt**:  
  *„The mouse sits down at the wooden kitchen table, places the cheese on a small plate, unwraps the brown paper with both paws and takes a big happy bite. Camera gently zooms in on its cheerful face.“*

---

## 8. Verknüpfte Leitfäden & Referenzen

* 🐭 [**Regie- & Drehbuch-Leitfaden: Das Maus-Projekt**](file:///home/clemi/Projekte/LLM/image-video-setup/anleitung_kurzfilm_maus_minimax.md)  
* 🎵 [**Anleitung: Audio & Ton in Videos integrieren**](file:///home/clemi/Projekte/LLM/image-video-setup/anleitung_audio_in_videos.md)  
* 💾 [**Leitfaden: Speicher- & VRAM-Management**](file:///home/clemi/Projekte/LLM/image-video-setup/modelle_direkt_entladen.md)  
* 📖 [**Ausführliches Gesamthandbuch**](file:///home/clemi/Projekte/LLM/image-video-setup/HANDBUCH_BILD_UND_VIDEO_KI.md)
