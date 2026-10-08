# Praxis-Leitfaden: ComfyUI Video-Workflows, VRAM-Management & Prompting

---

## 1. Bildschärfe & `ImageSharpen` bei Videos

### Warum `ImageSharpen` sich nicht direkt mit dem Video verbinden lässt:
* **Datentypen in ComfyUI:** 
  * Der Modell-Knoten `Image to Video (MiniMax H3)` gibt den Typ **`VIDEO`** aus (einen Videocontainer mit Video- und Audiospur).
  * Der Knoten `ImageSharpen` akzeptiert ausschließlich den Typ **`IMAGE`** (Bildtensor-Frames `[B, H, W, C]`).
  * Ein `VIDEO`-Ausgang kann nicht in einen `IMAGE`-Eingang gesteckt werden.

### So testest du Schärfe-Settings in 0,1 Sekunden (ohne Video-Rendern):
Teste den Schärfegrad direkt an deinem geladenen Standbild:
1. Ziehe ein Kabel vom `IMAGE`-Ausgang deines **`Load Image`**-Knotens in den Eingang von **`ImageSharpen`**.
2. Ziehe vom Ausgang von `ImageSharpen` ein Kabel in einen **`Preview Image`**-Knoten (`Doppelklick ➔ Preview Image`).
3. Klicke auf **Queue Prompt** ➔ das geschärfte Bild ist in **0,1 Sekunden** sichtbar!
4. Jetzt kannst du die Regler live justieren:
   * **`sharpen_radius`**: `1` (feine Poren, Wimpern, Haare) oder `2` (stärkere Kanten).
   * **`sigma`**: `1.0` bis `1.5`.
   * **`alpha`**: `0.20` bis `0.35` (nicht über `0.5`, sonst entstehen weiße Halo-Kanten / Bildrauschen).

### Wie du Schärfe ins Video einbindest:
* **Die eleganteste Methode ohne Zusatzknoten:** 
  Stelle im Knoten `Resolution Selector` den Wert `megapixels` auf **`0.98`** (das schöpft die native 768×1344p-Maximalauflösung von MiniMax H3 voll aus – das Video kommt bereits knackscharf aus dem Diffusionsmodell).
* **Falls du den Filter trotzdem fürs Video nutzen willst:** 
  Nutze den Knoten **`Split Video`** (oder `Get Video Components`):
  `MiniMax (VIDEO)` ──► `Split Video` ──► `images` ──► `ImageSharpen` ──► `CreateVideo` (mit dem Original-Audio verbinden) ──► `SaveVideo`.

---

## 2. Prompting für dynamische Bewegungen (z. B. Kampfpose)

Wenn das Startbild eine sitzende, ruhige Figur zeigt, kann sich die KI nicht sofort teleportieren. Du musst der KI die **Bewegungsabfolge (Transition)** beschreiben.

### ⚠️ Wichtigster Hebel: Negativen Prompt bereinigen!
Wenn im `negative`-Feld `fast motion, sudden movements` steht, **blockiert das dynamische Posen**.
* ❌ **Löschen:** `fast motion`, `sudden movements`.
* ✔️ **Gezielte Ausschlüsse:** `sitting down, staying seated, static, camera shake, distortion, morphing, warping, flickering, artifacts, face melting, extra limbs, deformed, blurry`.

### Optimaler Prompt für den Übergang in eine Kampfpose:

```text
positive
Dynamic cinematic action sequence, the divine celestial king suddenly rises aggressively from the golden throne, stepping forward with powerful authority. He raises his right hand, conjuring a blazing sphere of golden cosmic magic that crackles with divine energy. His luxurious blue and gold robes billow and whip dramatically in the surging magical wind. His glowing golden halo flares with intense radiant light. He lowers his center of gravity, smoothly shifting into a fierce, imposing martial arts combat stance, locking his glowing eyes aggressively on the opponent. Dynamic camera slightly pulling back to reveal his full fighting posture, dramatic rim lighting, epic fantasy anime battle scene, 4k cinematic lighting.

Audio: sudden loud surge of magical power, deep thunderous bass drop, fabric violently whipping in the wind, sharp crackle of divine celestial electricity, low menacing war hum.

negative
sitting down, staying seated, static, slow gentle breeze, peaceful, relaxed, distortion, morphing, warping, flickering, artifacts, identity drift, extra arms, deformed hands, blurry
```

---

## 3. VRAM vs. System-RAM: Warum stockte das System bei MiniMax H3?

### Die Bandbreiten-Realität:
* **VRAM (AMD Radeon PRO W7800):** **864 GB/s** (extrem schnell).
* **System-RAM (DDR5):** **50–70 GB/s**.
* **PCIe 4.0 Schnittstelle:** max. **31 GB/s**.
* **Festplatten-Swap (NVMe):** nur **1–3 GB/s**.

> **Ziel:** Wann immer möglich, zu 100 % im VRAM rechnen!

### Warum passte MiniMax H3 nicht komplett gleichzeitig in 48 GB VRAM?
MiniMax H3 besteht aus zwei separaten Riesenmodellen:
1. **Text- & Vision-Encoder (Qwen3-VL 32B):** **25,9 GB** (wird nur 2 Sekunden für den Prompt gebraucht).
2. **Video-Generator (FL2VA DiT):** **20,0 GB** (braucht man für die Diffusions-Schritte).
3. **Working Memory (Attention-Cache & Latents während des Rechnens):** **ca. 8 bis 10 GB**.

$$\underbrace{25{,}9\text{ GB}}_{\text{Text}} + \underbrace{20{,}0\text{ GB}}_{\text{Video}} + \underbrace{2{,}7\text{ GB}}_{\text{VAE}} + \underbrace{8{,}0\text{ GB}}_{\text{Cache}} = \mathbf{56{,}6\text{ GB VRAM}}$$

Auf einer 48-GB-Karte passen nicht beide Modelle gleichzeitig mit Rechenpuffer in den VRAM. ComfyUI **muss** sequentiell arbeiten:
* **Schritt 1:** Text analysieren (im VRAM).
* **Schritt 2:** Text-Encoder entladen, Video-Modell in den VRAM laden.

### Warum das System für 5 Minuten stockte (Die Swap-Falle):
ComfyUI versuchte, den 26 GB Text-Encoder "aufzuheben", indem es ihn in den PC-Arbeitsspeicher (RAM) verschob.
* Der 64 GB RAM füllte sich auf 60 GB.
* Linux begann, 20 GB auf die Festplatte (Swap) auszulagern.
* Das Verschieben von 25 GB über PCIe und Swap blockierte den Linux-Desktop für 5,5 Minuten.

### Die Lösung (bereits in `start_comfyui.sh` konfiguriert):
* **`--cache-ram 4 16`:** Begrenzt den inaktiven Modell-Cache im RAM auf maximal 16 GB.
* ComfyUI verwirft den Text-Encoder nach der Analyse, anstatt den gesamten RAM zu überfluten.
* **Ergebnis:** RAM bleibt unter 35 GB, kein Swap-Thrashing, der Desktop bleibt flüssig!

---

## 4. Modell-Vergleich: Welche Modelle bleiben 100 % im VRAM?

| Modell | Text-Encoder | Video-/Bild-Core | Rechen-Cache | Gesamt VRAM | Läuft 100 % im VRAM? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Alibaba Wan 2.1 (14B)** | 6,3 GB (UMT5-XXL) | 27,2 GB | 6,0 GB | **~39,5 GB** | **Ja! (Perfekt für 48 GB)** |
| **Flux.1 [dev]** | 4,8 GB (T5-XXL) | 17,2 GB | 6,0 GB | **~28,0 GB** | **Ja! (Kein RAM-Transfer)** |
| **SDXL Base 1.0** | 1,0 GB (CLIP-L/G) | 6,5 GB | 2,0 GB | **~9,5 GB** | **Ja! (Blitzschnell)** |
| **MiniMax H3** | 25,9 GB (Qwen 32B) | 20,0 GB | 8,0 GB | **~56,6 GB** | ❌ Nein *(Sequentieller Tausch)* |

* **Wan 2.1 und Flux** nutzen deine 48 GB VRAM optimal aus: Alle Komponenten bleiben permanent im VRAM, ohne ein einziges Byte in den normalen RAM auszulagern.
* **MiniMax H3** ist ein Sonderfall wegen des 32B-Multimodal-Encoders.

---

## 5. Warum stand der Sampler bei 0% („Es passiert nichts“)?

* In MiniMax H3 war der Schalter **`turbo_mode: false`**.
* Ohne Turbo rechnet das Modell **50 Schritte**.
* Ein einzelner Schritt dauert auf der W7800 ca. **40 Sekunden**.
* Die Prozentanzeige in ComfyUI springt **erst nach Abschluss von Schritt 1** um.
* Wer nach 2 Minuten abbricht, bricht genau während Schritt 1 ab (während die GPU mit 100 % Volllast rechnet).

### Die Lösung:
* Schalter **`turbo_mode: true`** im Knoten `Image to Video (MiniMax H3)` einschalten!
* Mit Turbo rechnet das Modell nur **8 Schritte** bei CFG 1.0.
* Der erste Schritt ist nach ca. 25 Sekunden durch (Fortschritt springt sofort auf 12 % ➔ 25 %...).
* Das gesamte Video ist in **ca. 2,5 Minuten** fertig.

---

## 6. VRAM-Cleanup: Wann ist es unnötig und wann zwingend notwendig?

Ein häufiges Missverständnis ist die Frage, ob nach jeder Generierung ein `VRAM-Cleanup`-Knoten verwendet werden sollte. Die klare technische Antwort lautet: **Nein!**

---

### A. Bei ausschließlicher Arbeit mit EINEM Modell (Wan, FLUX, SDXL, Qwen-Image): VRAM-Cleanup ist VÖLLIG UNNÖTIG

* **Die Speicher-Realität:**  
  Alle diese Modelle passen inklusive Text-Encoder und VAE komplett in die 48 GB VRAM deiner AMD Radeon PRO W7800:
  * **SDXL:** ~6–8 GB VRAM (zu 100 % im VRAM)
  * **Qwen-Image-2.1:** ~18–22 GB VRAM (zu 100 % im VRAM)
  * **FLUX.1 [dev]:** ~20–24 GB VRAM (zu 100 % im VRAM)
  * **Wan 2.1 / Wan 2.2:** ~24–38 GB VRAM (zu 100 % im VRAM)
* **Warum VRAM-Cleanup hier schadet:**  
  Wird nach jedem Durchlauf ein `VRAM-Cleanup`-Knoten ausgeführt, löscht ComfyUI alle Modellgewichte. Beim nächsten Klick auf *Run* müssen 10 bis 35 GB erneut von der NVMe-SSD in den VRAM transferiert werden. Das kostet **jedes Mal 15 bis 60 Sekunden unnötige Wartezeit**!
* **Best Practice:**  
  **Keinen `VRAM-Cleanup`-Knoten verwenden!** Die Modelle bleiben im VRAM gecacht. Folge-Generierungen (neue Prompts, andere Posen oder Seeds) starten in **0 Sekunden** ohne jegliche Ladezeit direkt mit dem Sampler.

---

### B. Wann VRAM-Cleanup tatsächlich sinnvoll & notwendig ist (Die 2 Ausnahmen):

#### Ausnahme 1: Nur bei einem echten MODELL-WECHSEL
* Wenn du von einer Modell-Architektur zu einer völlig anderen wechselst:
  * Beispiel: Von **Wan 2.2** ➔ zu **MiniMax H3** (oder von **FLUX** ➔ zu **Wan**).
* **Warum hier:** Damit alte, inaktive Gewichte der vorherigen Modell-Familie den VRAM nicht blockieren und das neue Modell saubere, unfragmentierte 48 GB vorfindet.
* **Empfohlene Methode:** Vor dem Wechsel im ComfyUI-Menü oben rechts einfach einmal auf **`Unload Models`** klicken.

#### Ausnahme 2: Bei MiniMax H3 – Die einzige Modell-Familie über 48 GB
* **Das Problem bei MiniMax H3:**  
  MiniMax nutzt den gigantischen 26 GB Text- & Bild-Encoder (`qwen3vl_32b`). Zusammen mit dem 20 GB DiT-Kern übersteigt das Gesamtgewicht (~54–56 GB) die 48 GB VRAM deiner Karte!
* **Der Ablauf:**  
  1. Zuerst wird das Startbild und der Text vom 26 GB VLM-Encoder verarbeitet.
  2. **Direkt nach dem Bild-Laden / Prompting:** Der 26 GB Text-Encoder **muss** aus dem VRAM weichen, um Platz für das 20 GB Diffusionsmodell zu machen. ComfyUI regelt diesen Übergang intern.
  3. **Nach Fertigstellung des Videos:** MiniMax sollte mit **`Unload Models`** (oder einem Cleanup-Knoten am Videoausgang) entladen werden, damit der 26 GB Brocken nicht dauerhaft im Host-RAM verweilt und den Desktop blockiert.

---

### 📋 Zusammenfassende Faustregel:

| Szenario | VRAM-Cleanup nötig? | Begründung |
| :--- | :---: | :--- |
| **Nur Wan 2.1 / Wan 2.2 nutzen** | ❌ **NEIN (Unnötig)** | Passt zu 100 % in 48 GB. Gecacht lassen für **0s Ladezeit** bei Folgebildern. |
| **Nur FLUX.1 [dev] / SDXL nutzen** | ❌ **NEIN (Unnötig)** | Passt locker in 48 GB (6–24 GB). Folgebilder starten in 1–3 Sekunden. |
| **Nur Qwen-Image-2.1 nutzen** | ❌ **NEIN (Unnötig)** | Passt mit ~18 GB komplett in 48 GB. Keine Neuladezeit nötig. |
| **Zwischen Modellen wechseln** (z. B. Wan ➔ MiniMax) | ✅ **JA (Sinnvoll)** | Einmalig `Unload Models` klicken, um alten Speicherplatz restlos freizugeben. |
| **MiniMax H3 nach Generierung** | ✅ **JA (Empfohlen)** | Einziges Modell > 48 GB. Verhindert, dass der 26 GB Text-Encoder den System-RAM blockiert. |

## 7. Modell-Profile im Vergleich: Wan 2.2 vs. MiniMax H3 vs. Qwen-Image-2.1

| Modell | Typ | Speicher-Architektur | VRAM-Peak (48 GB W7800) | RAM-Belastung | Besonderheit & Sweet Spot |
| :--- | :---: | :--- | :---: | :---: | :--- |
| **Alibaba Wan 2.2** | 🎬 Video | **Dual DiT (14B fp8):**<br>• High-Noise (13,3 GB)<br>• Low-Noise (13,3 GB)<br>• UMT5-XXL (6,3 GB) | **~35 – 40 GB**<br>*(100 % im VRAM)* | **Minimal (< 6 GB)** | **Bester Video-Allrounder:** Beide Diffusionsmodelle bleiben permanent im VRAM. 4-Step Turbo rendert Clips in unter 90s ohne PCIe-Swaps. |
| **MiniMax H3** | 🎬 Video | **Omni DiT (16B int8) + VLM:**<br>• Qwen3-VL 32B (25,9 GB)<br>• DiT Core (19,5 GB)<br>• Dual VAE (Video + Audio) | **> 48 GB Gesamtgewicht**<br>*(Sequentieller Tausch)* | **Sehr hoch (bis 60 GB)**<br>*(Erfordert `--cache-ram`)* | **Einzigartig durch natives Stereo-Audio:** Erzeugt Bild + Soundeffekte synchron in einem Durchlauf. Braucht Turbo-LoRA. |
| **Alibaba Wan 2.1** | 🎬 Video | **Single DiT (14B fp8/bf16):**<br>• DiT Core (14–27 GB)<br>• UMT5-XXL (6,3 GB) | **~24 – 38 GB**<br>*(100 % im VRAM)* | **Minimal (< 6 GB)** | Bewährter Vorgänger, sehr stabile Kamerabewegungen, benötigt 20–30 Schritte. |
| **Qwen-Image-2.1** | 🖼️ Bild | **SOTA DiT (int8_convrot):**<br>• Diffuser (6,8 GB)<br>• Text-Encoder (8,7 GB)<br>• Prompt-Enhancer (8,9 GB) | **~18 – 22 GB**<br>*(100 % im VRAM)* | **Minimal (< 5 GB)** | **Weltbeste Typografie & Schriften im Bild.** Native 2K-Ausgabe, transparente PNGs (RGBA) und Prompt-Reasoning. |

---

## 8. Optimierung der ComfyUI-Einstellungen (`start_comfyui.sh`)

Für eine stabile Workstation mit **AMD Radeon PRO W7800 (48 GB VRAM)**, **64 GB System-RAM** und **ROCm 6.4** sind folgende Parameter in `start_comfyui.sh` konfiguriert:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source comfy_env/bin/activate
cd ComfyUI

# 1. ROCm / PyTorch Speicher-Optimierungen:
# Verhindert VRAM-Fragmentierung bei riesigen Modellen:
export PYTORCH_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"
export PYTORCH_CUDA_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"

# Vermeidet SDMA-Hardware-Ring Deadlocks bei PCIe-Transfers auf RDNA3:
export HSA_ENABLE_SDMA=0

# 2. ComfyUI Startparameter:
# --reserve-vram 3 : Schützt 3 GB VRAM für den Desktop (GNOME/Wayland/Monitore)
# --cache-ram 4 16 : Begrenzt inaktive Modelle im RAM (4 GB aktiv, 16 GB max) -> Verhindert Swap-Thrashing!
exec python main.py --reserve-vram 3 --cache-ram 4 16 --listen 0.0.0.0 --port 8188
```

### Die Wirkung der Einstellungen im Detail:
1. **`--cache-ram 4 16` (Die Rettung vor dem 60 GB RAM-Freeze):**
   * *Problem:* Standardmäßig pinnt ComfyUI unbegrenzt Modelle im System-RAM. Wenn MiniMax den 26 GB Text-Encoder in den RAM schob, explodierte der RAM-Verbrauch von 30 GB auf 60 GB und löste 20 GB Swap auf der NVMe-SSD aus.
   * *Lösung:* Durch `4 16` darf ComfyUI maximal 16 GB inaktive Modelle im RAM parken. Überschüssige Gewichte werden verworfen. Der Host-RAM bleibt stets unter 35 GB.
2. **`--reserve-vram 3`:**
   * Garantiert, dass der Linux-Desktop, 4K-Monitore und Browserfenster immer 3 GB unantastbaren Grafikspeicher haben. Verhindert Blackscreens bei VRAM-Spitzen.
3. **`HSA_ENABLE_SDMA=0`:**
   * Schaltet auf AMD RDNA3 Grafikkarten den SDMA-Transfer-Ring ab und erzwingt sichere Compute-Shader-Transfers. Verhindert GPU-Treiber-Crashes bei massiven Modellwechseln über PCIe.
4. **`PYTORCH_ALLOC_CONF="garbage_collection_threshold:0.8,max_split_size_mb:512"`:**
   * Sorgt dafür, dass PyTorch seinen internen Speicherpool bei 80 % Füllstand aufräumt und Speicherblöcke nicht in winzige Fragmente zerfallen.

---

## 9. Der Turbo-Modus: Technische Bedeutung, Qualitätsbewertung & Konfigurationsregeln

### A. Was ist der Turbo-Modus technisch? (Model Distillation)
Herkömmliche Diffusionsmodelle erzeugen Bilder und Videos schrittweise aus Gaußschem Rauschen über eine Trajektorie von **20 bis 50 Einzelschritten** (z. B. mit Euler- oder UniPC-Samplern).

Beim **Turbo-Verfahren** (auch als *Lightning*, *Hyper* oder *Adversarial Distillation* bezeichnet):
* Ein separates Student-Modell oder LoRA lernt durch Wissensdestillation, die Vorhersage mehrerer kleiner Schritte in **wenige große Schritte** zusammenzufassen.
* Anstatt 50 Einzelschritte zu berechnen, genügen **4 oder 8 Schritte**.
* **Beschleunigungsfaktor:** Die Rechenzeit sinkt um **75 % bis 90 %** (z. B. von 33 Minuten auf 2,5 Minuten bei MiniMax H3 oder von 8 Minuten auf unter 90 Sekunden bei Wan 2.2).

### B. Was bringt der Turbo-Modus in der Praxis?
1. **Dramatisch schnellere Iterationszyklen:**
   * Prompts, Kamerawinkel, Lichtstimmungen und Kampfposen können innerhalb von 60–90 Sekunden getestet und angepasst werden, anstatt nach jedem Klick 20 Minuten warten zu müssen.
2. **Reduzierte System- und GPU-Dauerbelastung:**
   * Die GPU rechnet nur kurzzeitig unter Volllast, wodurch Leistungsaufnahme, Wärmeentwicklung und Lüfterlautstärke der Workstation drastisch sinken.
3. **Verhinderung von System-Timeouts und Engpässen:**
   * Kürzere Rechenzeiten minimieren das Risiko von Speicherfragmentierung und Treiberkonflikten bei langen Render-Sessions.

### C. Einfluss auf die Bild- und Videoqualität (Die ehrliche Abwägung)

| Qualitätsaspekt | Standard-Modus (20–50 Schritte) | Turbo-Modus (4–8 Schritte) | Bewertung im Video |
| :--- | :--- | :--- | :--- |
| **Kamerabewegung & Physik** | 100 % | **98 %** | Praktisch identisch, keine Nachteile |
| **Anatomie & Posenwechsel** | 100 % | **98 %** | Nahezu identisch, saubere Übergänge |
| **Farbdynamik & Beleuchtung**| 100 % | **95 %** | Sehr gut, erfordert jedoch zwingend CFG 1.0 |
| **Mikro-Details (Hautporen, feines Haar)** | 100 % (maximale Schärfe) | **90–92 %** (minimal weicher) | Bei 16–24 FPS für das Auge kaum wahrnehmbar |
| **Rechenzeit (Wan 2.2)** | ~6 bis 8 Minuten | **~60 bis 90 Sekunden** | **5- bis 8-mal schneller** |
| **Rechenzeit (MiniMax H3)** | ~33 Minuten | **~2,5 Minuten** | **13-mal schneller** |

*Fazit:* Für Videosequenzen ist der minimale Schärfeverlust von ca. 5 % bei bewegten Bildern vernachlässigbar. Der Turbo-Modus ist für den Arbeitsalltag der Standardmodus.

### D. Die zwei zwingenden Konfigurationsregeln für Turbo-Modelle

Sobald ein Turbo-LoRA oder Turbo-Schalter aktiviert wird, müssen zwei Parameter zwingend beachtet werden:

1. **CFG (Guidance Scale) MUSS auf 1.0 gesetzt werden:**
   * *Problem:* Im Standardmodus arbeitet CFG typischerweise bei 3.5 bis 7.0 (positive und negative Prompts werden getrennt berechnet). Im Turbo-Modus führt ein CFG über 1.5 zu schweren Artefakten, Farbverbrennungen und verformten Gesichtern.
   * *Lösung:* Im Turbo-Betrieb gilt strikt **`cfg: 1.0`** (bzw. max. `1.5`). Bei CFG 1.0 entfällt zudem die doppelte Rückwärtspass-Berechnung, was die Inferenz zusätzlich beschleunigt.
2. **Die Schrittzahl (`steps`) MUSS exakt der LoRA-Spezifikation entsprechen:**
   * Bei 4-Step-LoRAs: **exakt 4 Schritte**.
   * Bei 8-Step-LoRAs: **exakt 8 Schritte**.
   * *Hinweis:* Wird einem 4-Step-LoRA eine Schrittzahl von 20 zugewiesen, wird die Bildinformation rechnerisch übersteuert und zerstört.

### E. Modell-spezifische Einstellungen

| Modell | Schalter / LoRA | Schritte | CFG | Rechenzeit (W7800) |
| :--- | :--- | :---: | :---: | :--- |
| **Wan 2.2 Turbo** | `enable_turbo_mode: true`<br>(nutzt `lightx2v_4steps` High- & Low-Noise LoRAs) | **4**<br>(Split bei 2) | **1.0** | **~60–90 Sekunden** |
| **Wan 2.2 Standard** | `enable_turbo_mode: false` | **20**<br>(Split bei 10) | **3.5** | **~6–8 Minuten** |
| **MiniMax H3 Turbo** | `turbo_mode: true`<br>(nutzt `minimax_h3_fl2v_turbo_8step...`) | **8** | **1.0** | **~2,5 Minuten** |
| **MiniMax H3 Standard**| `turbo_mode: false` | **50** | **3.5** | **~33 Minuten** |
| **FLUX.1 [dev] Hyper**| `Hyper-FLUX.1-dev-8steps-lora` | **8** | **1.0** | **~3–4 Sekunden** |
| **SDXL Lightning** | `sdxl_lightning_4step_lora` | **4** | **1.5** | **~1–2 Sekunden** |

### F. Der optimale 2-Phasen Workflow
* **Phase 1 (Entwurf & Exploration):** Konsequente Nutzung des **Turbo-Modus**. Überprüfung von Posen, Bildausschnitt, Timing und Regieanweisungen in Sekundenschnelle.
* **Phase 2 (Finaler Master-Shot - Optional):** Nach erfolgreicher Validierung aller Bewegungsabläufe kann für das finale Master-Rendering auf den Standardmodus umgeschaltet werden, um das Maximum an Sub-Pixel-Schärfe zu erzielen.


