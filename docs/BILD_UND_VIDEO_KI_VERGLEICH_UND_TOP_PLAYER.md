# 🎬🎨 Vergleichsmatrix: Bild- & Video-Generierungsmodelle (Lokal vs. Cloud Top-Player)

> **Hardware-Basis:** AMD Radeon Pro W7800 (48 GB GDDR6 VRAM, ~45,0 GiB netto nutzbar) + 61 GB System-RAM + ROCm 6.4 nativ  
> **Server-Umgebung:** ComfyUI v0.3.x (Port 8188) | Open WebUI  
> **Besonderheit:** Dank **48 GB VRAM** kann dieses System riesige Video-DiTs (Wan 2.2 Dual DiT, MiniMax H3) und High-End Diffusionsmodelle (FLUX.1 [dev] mit ControlNet) vollständig im VRAM ausführen – ohne Abstürze und ohne PCIe-Bottlenecks.

---

## 🎨 1. BILD-GENERATOREN: Lokale Modelle vs. Cloud-Giganten

*Nahtloses Ranking aller Modelle nach Gesamtqualität (Skala 1–10, 10 = absolute Weltspitze)*

| Rang & Modell | Status / Umgebung | Architektur & Parameter | Primärer Fokus / Spezialisierung | Fotorealismus (1-10) | Kreativität & Stile (1-10) | Typografie / Text (1-10) | Kontrolle & LoRA (1-10) | Renderzeit auf W7800 | VRAM-Bedarf | Kosten & Lizenz | Gesamt Score (100) |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 **Midjourney v6 / v7** | 🌐 Cloud (Midjourney) | Proprietär (Mega-Cluster) | **Ästhetik, Lichtstimmung, Komposition & Fotokunst** | **9.9** 🥇 | **9.9** 🥇 | 8.8 | 8.0 | ~30–60s *(Cloud)* | 0 GB | Ab 10–60 $/Monat | **97 / 100** |
| 🥈 **FLUX.2** *(Dev FP8)* | ✅ **Bei dir installiert** | 24B DiT (BFL Next-Gen) | **Multi-Referenz-Konsistenz:** Bis zu 10 Referenzbilder | **9.8** | 9.5 | 9.3 | **9.8** 🥇 | ⚡ **~12–18s** *(Turbo-LoRA)*<br>~28s *(Standard)* | 34–40 GB | **0,00 € (Lokal)** | **95 / 100** |
| 🥉 **Qwen-Image-2.1** | ✅ **Bei dir installiert** | 9B DiT (`int8_convrot`) | **Layout & Typografie:** Sätze, Schilder, native 2K/RGBA | 9.5 | **9.7** | **9.9** 🥇 | 9.4 | ~12–16s | 18–22 GB | **0,00 € (Lokal)** | **94 / 100** |
| 4. **FLUX.1 [dev]** | ✅ **Bei dir installiert** | 12B DiT (`fp8`) | **High-End Detail-Referenz:** Natürliche Haut, Hände, Licht | 9.6 | 9.2 | 9.3 | 9.5 | ~20–25s | 17–24 GB | **0,00 € (Lokal)** | **93 / 100** |
| 5. **Ideogram v2 / v3** | 🌐 Cloud (Ideogram) | Proprietär (Cloud) | **Plakate, T-Shirt-Designs, Logos & Grafik-Typo** | 8.8 | 9.4 | **9.9** 🥇 | 7.5 | ~15–30s *(Cloud)* | 0 GB | Freemium (Cloud) | **92 / 100** |
| 6. **HunyuanImage 3.0** | 💡 **Lokal möglich** | 13B DiT (Tencent) | **Harmonische Komposition, asiatische & westliche Kunst** | 9.6 | 9.5 | 9.2 | 9.3 | ~22–28s | 24–32 GB | Open Weights (Gratis) | **92 / 100** |
| 7. **Imagen 3** | 🌐 Cloud (Google) | DeepMind Diffusions-Modell | **Weiche Beleuchtung, fotorealistische Tier- & Naturwelten** | 9.6 | 9.0 | 9.1 | 7.8 | ~10–20s *(Cloud)* | 0 GB | Pay-per-Image | **91 / 100** |
| 8. **DALL-E 3** | 🌐 Cloud (OpenAI) | DALL-E (ChatGPT Plus) | **Prompt-Treue:** Versteht komplexe Satzkonstruktionen | 8.5 | 9.2 | 9.2 | 7.0 | ~15–25s *(Cloud)* | 0 GB | Im ChatGPT-Abo | **89 / 100** |
| 9. **Juggernaut XL (v9/v10)**| ✅ **Bei dir installiert** | SDXL Checkpoint (6.6 GB) | **35mm Analogfilm, Kinolook & RED/Arri-Porträts** | **9.3** | 8.6 | 6.5 | 9.2 | ⚡ **~3–5s** | 8–12 GB | **0,00 € (Lokal)** | **88 / 100** |
| 10. **FLUX.1 [schnell]** | ✅ **Bei dir installiert** | 12B DiT (4 Steps) | **Interaktive Highspeed-Bilder für Web-Chats (Open WebUI)** | 9.2 | 8.8 | 9.0 | 8.5 | ⚡ **~4–6s** | 16–20 GB | **0,00 € (Lokal)** | **87 / 100** |
| 11. **SD 3.5 Large** | ✅ **Bei dir installiert** | 8B MMDiT (`fp8`) | **Grafikdesign, Typografie, Poster & Vektor-Illustration** | 8.8 | 9.3 | 8.4 | 9.5 | ~18–22s | 16–24 GB | **0,00 € (Lokal)** | **87 / 100** |
| 12. **Pony Diffusion V6 XL** | 💡 **Lokal möglich** | SDXL Finetune (6.5 GB) | **Anime, Manga, Comics & stark stilisierte Charaktere** | 7.2 | **9.6** | 6.0 | 8.9 | ⚡ **~4–6s** | 10–14 GB | Open Weights (Gratis) | **83 / 100** |
| 13. **SDXL Base 1.0** | ✅ **Bei dir installiert** | SDXL Standard (6.5 GB) | **Gigantisches Civitai LoRA-Ökosystem für jeden Nischenstil** | 8.0 | 8.8 | 6.5 | 9.2 | ⚡ **~3–5s** | 7–10 GB | **0,00 € (Lokal)** | **81 / 100** |

---

## 🎥 2. VIDEO-GENERATOREN: Lokale Modelle vs. Cloud-Giganten

*Nahtloses Ranking aller Modelle nach Bewegung, Physik und Kinotauglichkeit (Skala 1–10)*

| Rang & Modell | Status / Umgebung | Architektur | Primärer Fokus / Spezialisierung | Bewegung & Physik (1-10) | Cineastik & Bildschärfe (1-10) | Prompt- & Kamera-Treue (1-10) | Audio / Tonspur (1-10) | Renderzeit auf W7800 | VRAM-Bedarf | Kosten & Lizenz | Gesamt Score (100) |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 **OpenAI Sora / Turbo** | 🌐 Cloud (OpenAI) | Multi-GPU Cloud DiT | **Cineastische Großprojekte, epische Kamerafahrten, 1080p** | **9.9** 🥇 | **9.9** 🥇 | **9.8** 🥇 | 7.5 *(Teils Audio)*| ~2–5m *(Queue)* | 0 GB | Teures Cloud-Abo | **98 / 100** |
| 🥈 **Alibaba Wan 2.2** | ✅ **Bei dir installiert** | **Dual DiT** *(14B High+Low)* | **Beste lokale Physik:** Dual DiT + 4-Step Turbo-LoRA | **9.8** | **9.8** | 9.6 | 6.0 *(Stumm)* | ⚡ **~60–90s** *(Turbo)*<br>~7m *(Standard)* | 35–40 GB | **0,00 € (Lokal)** | **96 / 100** |
| 🥉 **Runway Gen-3 Alpha** | 🌐 Cloud (Runway) | Proprietär (Cloud) | **VFX-Industriestandard, Kinobeleuchtung & Regie-Tools** | 9.7 | 9.8 | 9.5 | 7.0 *(Basissound)*| ~1–3m *(Cloud)* | 0 GB | Ab 12–76 $/Monat | **95 / 100** |
| 4. **MiniMax H3 (Hailuo 03)**| ✅ **Bei dir installiert** | **Omni DiT** *(Video+Audio)* | **Kino-Video MIT nativer Stereo-Tonspur (Sprache/Sound)** | 9.4 | 9.7 | 9.3 | **9.8** 🥇 | ⚡ **~2,5m** *(Turbo)*<br>~33m *(Standard)* | 24–42 GB | **0,00 € (Lokal)** | **95 / 100** |
| 5. **Kling 1.5 / 2.0** | 🌐 Cloud (Kuaishou) | Cloud DiT Cluster | **Dynamische menschliche Posen, Mimik & Akrobatik** | 9.6 | 9.7 | 9.4 | 6.5 *(Stumm)* | ~1–4m *(Cloud)* | 0 GB | Ab 10–50 $/Monat | **94 / 100** |
| 6. **HunyuanVideo** | 💡 **Lokal möglich** | 13B Video-DiT (Tencent) | **Gesichter & Filmkamera:** Extrem feine Gesichtsdetails | 9.3 | **9.8** | 9.2 | 6.0 *(Stumm)* | ~8–12m | 24–40 GB | Open Weights (Gratis) | **93 / 100** |
| 7. **Luma Dream Machine** | 🌐 Cloud (Luma) | Proprietär (Cloud) | **Dynamische 3D-Kamerabewegungen & rasante Verfolgungsjagden** | 9.5 | 9.4 | 9.2 | 6.0 *(Stumm)* | ~1–3m *(Cloud)* | 0 GB | Freemium (Cloud) | **93 / 100** |
| 8. **Alibaba Wan 2.1 (14B)** | ✅ **Bei dir installiert** | 14B Video-DiT | **Physikalische Simulation:** Wasser, Stoffe, Schwerkraft | **9.8** | 9.6 | 9.4 | 6.0 *(Stumm)* | ~6–8m *(Standard)* | 28–44 GB | **0,00 € (Lokal)** | **93 / 100** |
| 9. **Mochi 1** | 💡 **Lokal möglich** | 10B DiT (Genmo) | **30fps Bewegungsdynamik:** Extrem flüssige Animationen | 9.5 | 8.9 | 9.0 | 6.0 *(Stumm)* | ~10–14m | 38–44 GB | Open Weights (Gratis) | **89 / 100** |
| 10. **CogVideoX-5B** | 💡 **Lokal möglich** | 5B 3D DiT (THUDM) | **Solider Text-to-Video Coder mit moderatem VRAM-Bedarf** | 8.8 | 8.7 | 8.8 | 6.0 *(Stumm)* | ~3–5m | 18–26 GB | Open Weights (Gratis) | **86 / 100** |
| 11. **LTX-Video 2B** | ✅ **Bei dir installiert** | 2B Highspeed DiT | **Highspeed-Prototyping:** 24fps Text/Image-to-Video Clips | 8.4 | 8.2 | 8.5 | 6.0 *(Stumm)* | 🚀 **~12–20s** | 10–16 GB | **0,00 € (Lokal)** | **84 / 100** |
| 12. **Stable Video Diff (SVD)**| ✅ **Bei dir installiert** | UNet (25 Frames) | **Sanfte Kamerafahrten für Standbilder (Image-to-Video)** | 8.0 | 8.5 | 8.0 | 6.0 *(Stumm)* | ~35–50s | 9–14 GB | **0,00 € (Lokal)** | **80 / 100** |

---

## 💡 3. Welche Modelle sind auf deiner W7800 NOCH möglich? (Upgrade-Potenzial)

Dank deiner **48 GB VRAM** kannst du Open-Weights-Modelle herunterladen, an denen fast alle Consumer-Grafikkarten (RTX 4080/4090 mit nur 16–24 GB) scheitern:

### 🌟 Noch mögliche BILD-Modelle (Upgrade-Optionen):

> ℹ️ **Hinweis:** **FLUX.2 [dev]** ist bereits vollständig auf deiner Workstation installiert (34 GB DiT + 17 GB Text-Encoder + Turbo-LoRA)!

1. **`HunyuanImage 3.0` (Tencent):**
   * **Warum downloaden?** Tencents 13B Flaggschiff. Brilliert bei komplexen Mehr-Personen-Szenen, Hintergründen und asiatischen Stilen, an denen FLUX manchmal scheitert.
   * **Hardware-Bedarf:** ~28 GB VRAM.

2. **`Pony Diffusion V6 XL`:**
   * **Warum downloaden?** Das weltweite Standardmodell auf Civitai für Anime, Manga, Cartoons und dynamische Action-Posen. Läuft mit **~4 Sekunden** rasant schnell im VRAM.
   * **Hardware-Bedarf:** Nur ~10 GB VRAM.

3. **`AuraFlow v0.3` (12B Open-Source DiT):**
   * **Warum downloaden?** Vollständig offenes 12B Diffusions-Transformer-Modell ohne restriktive Non-Commercial-Klauseln.
   * **Hardware-Bedarf:** ~20–26 GB VRAM.

---

### 🎥 Noch mögliche VIDEO-Modelle:

1. **`HunyuanVideo` (Tencent - 13B Parameter):**
   * **Warum downloaden?** Neben Wan 2.2 das stärkste Open-Source-Videomodell der Welt. Während Wan 2.2 unschlagbar bei Wasser, Rauch und Natur ist, hat HunyuanVideo die **feinsten menschlichen Gesichter, Blicke und Lippenbewegungen**.
   * **Hardware-Bedarf:** 24–40 GB VRAM – passt zu 100% in deine W7800!

2. **`Mochi 1` (Genmo - 10B Parameter):**
   * **Warum downloaden?** Rendert mit echten **30 Bildern pro Sekunde (30fps)**. Bewegungen sehen dadurch extrem organisch und flüssig aus (kein "Slow-Motion-Look" wie bei älteren Modellen).
   * **Hardware-Bedarf:** ~40 GB VRAM. (Nahezu unmöglich auf 24 GB Karten, läuft aber auf deiner W7800!).

3. **`CogVideoX-5B` (THUDM):**
   * **Warum downloaden?** Extrem robuster Text-to-Video-Allrounder für schnelle 6-Sekunden-Clips in 3–5 Minuten.
   * **Hardware-Bedarf:** ~22 GB VRAM.

---

## 🎯 4. Praxis-Leitfaden: Was nutzt du für welches Vorhaben?

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                      DER OPTIMALE MEDIEN-WORKFLOW                              │
├────────────────────────────────────────────────────────────────────────────────┤
│ 1. Fotorealistisches Porträt oder Produktbild?                                 │
│    ──> `FLUX.1 [dev]` (Unübertroffene Hautporen, Beleuchtung & Hände)          │
│                                                                                │
│ 2. Bild mit Schildern, Schriftzügen, Speisekarte oder Logo?                    │
│    ──> `Qwen-Image-2.1` (Weltbester Text-im-Bild-Renderer, 9.9 Punkte)         │
│                                                                                │
│ 3. Sofortbild in unter 5 Sekunden für Chats?                                   │
│    ──> `FLUX.1 [schnell]` (4 Steps) oder `Juggernaut XL` (35mm Kinolook)       │
│                                                                                │
│ 4. Cineastisches Video mit atemberaubender Physik & Bewegung?                  │
│    ──> `Wan 2.2 Dual DiT` (Mit 4-Step Turbo in 75 Sekunden fertig!)            │
│                                                                                │
│ 5. Video, das sofort sprechen oder Musik/Sound haben soll?                     │
│    ──> `MiniMax H3` (Erzeugt Video + synchrone Tonspur in 2,5 Minuten)         │
│                                                                                │
│ 6. Schnelles 15-Sekunden-Video zum Testen von Bildideen?                       │
│    ──> `LTX-Video 2B` (In 15 Sekunden fertig zum Vorab-Check)                  │
│                                                                                │
│ 7. Freistellen, Hintergründe entfernen & Transparenz?                          │
│    ──> `RMBG-2.0` (In 0,8 Sekunden saubere Alphamaske für Haare & Kanten)     │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 💰 Was sparst du durch dein lokales Setup?
* Ein Midjourney-Abo (Pro) kostet **60 $/Monat**.
* Ein Runway Gen-3 / Sora-Kontingent für Videoerstellung kostet **50–100 $/Monat**.
* Mit deiner **AMD Radeon Pro W7800** generierst du Bilder und Videos in **Cloud-Spitzenqualität** beliebig oft, ohne monatliche Abos, ohne Zensur-Einschränkungen und absolut vertraulich auf deiner eigenen Workstation!

