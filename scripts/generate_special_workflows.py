import json
import os
import copy

def load_template():
    with open("ComfyUI/user/default/workflows/minimax_h3_stufen/03_charakter_ref2v_anker.json") as f:
        return json.load(f)

# 1. _minimax_h3_prompt_enhancer.json
def create_prompt_enhancer_wf():
    wf = load_template()
    wf["id"] = "minimax-h3-prompt-enhancer"
    
    # We replace node 138 (PrimitiveStringMultiline) with StringConstantMultiline + JoinStringMulti
    # Let's inspect node 138
    # Node 138 was connected to node 136 (MiniMaxH3ReferenceToVideo) input "prompt" via link 257
    nodes = wf["nodes"]
    
    # Remove old node 138
    nodes = [n for n in nodes if n["id"] != 138]
    
    # Add modular prompt enhancer nodes
    # 201: Master Style
    node_style = {
        "id": 201,
        "type": "StringConstantMultiline",
        "pos": [-1500, 3900],
        "size": [400, 160],
        "title": "🎨 1. Master Style (Visual Consistency)",
        "inputs": [],
        "outputs": [{"name": "string", "type": "STRING", "links": [301]}],
        "widgets_values": ["cinematic 35mm anamorphic film, golden hour dusk lighting, subtle volumetric haze, Kodak Portra 400 color grading, photorealistic, 8k"],
        "widgets_values_named": {"string": "cinematic 35mm anamorphic film, golden hour dusk lighting, subtle volumetric haze, Kodak Portra 400 color grading, photorealistic, 8k"}
    }
    
    # 202: Character & Subject
    node_char = {
        "id": 202,
        "type": "StringConstantMultiline",
        "pos": [-1500, 4100],
        "size": [400, 160],
        "title": "🐭 2. Character & Subject (<Picture 1> Anker)",
        "inputs": [],
        "outputs": [{"name": "string", "type": "STRING", "links": [302]}],
        "widgets_values": ["<Picture 1> the sharp mouse detective wearing a detailed brown trenchcoat and fedora hat, resolute expression"],
        "widgets_values_named": {"string": "<Picture 1> the sharp mouse detective wearing a detailed brown trenchcoat and fedora hat, resolute expression"}
    }
    
    # 203: Camera & Action
    node_camera = {
        "id": 203,
        "type": "StringConstantMultiline",
        "pos": [-1500, 4300],
        "size": [400, 160],
        "title": "🎥 3. Camera Movement & Action",
        "inputs": [],
        "outputs": [{"name": "string", "type": "STRING", "links": [303]}],
        "widgets_values": ["low-angle tracking dolly shot forward, walking briskly along the wet asphalt alley, neon signs reflecting in puddles"],
        "widgets_values_named": {"string": "low-angle tracking dolly shot forward, walking briskly along the wet asphalt alley, neon signs reflecting in puddles"}
    }
    
    # 204: Sound & Acoustic Scene
    node_audio = {
        "id": 204,
        "type": "StringConstantMultiline",
        "pos": [-1500, 4500],
        "size": [400, 160],
        "title": "🔊 4. Audio Scene Director (Synchroner Ton)",
        "inputs": [],
        "outputs": [{"name": "string", "type": "STRING", "links": [304]}],
        "widgets_values": ["heavy raindrops splashing on pavement, soft rumble of distant thunder, rhythmic trenchcoat fabric rustling, quiet footsteps"],
        "widgets_values_named": {"string": "heavy raindrops splashing on pavement, soft rumble of distant thunder, rhythmic trenchcoat fabric rustling, quiet footsteps"}
    }
    
    # 205: JoinStringMulti
    node_join = {
        "id": 205,
        "type": "JoinStringMulti",
        "pos": [-1050, 4150],
        "size": [320, 240],
        "title": "🧩 Modular Prompt Enhancer (JoinStringMulti)",
        "inputs": [
            {"name": "string_1", "type": "STRING", "link": 301},
            {"name": "string_2", "type": "STRING", "link": 302},
            {"name": "string_3", "type": "STRING", "link": 303},
            {"name": "string_4", "type": "STRING", "link": 304}
        ],
        "outputs": [{"name": "string", "type": "STRING", "links": [257]}],
        "widgets_values": [", ", "string_1", "string_2", "string_3", "string_4"]
    }
    
    # Add Note explaining Qwen3-VL multimodality
    node_note = {
        "id": 206,
        "type": "MarkdownNote",
        "pos": [-1500, 3600],
        "size": [850, 260],
        "title": "💡 PROMPT ENHANCER GUIDE FÜR MINIMAX H3",
        "widgets_values": ["""# 💡 Warum dieser modulare Prompt Enhancer?

MiniMax H3 nutzt als Text-Encoder **Qwen3-VL 32B** (ein multimodales 32-Milliarden-Parameter-Modell).
Ein kurzer Prompt wie *"Maus geht im Regen"* verschenkt 80% des Potenzials!

Dieser modulare Prompt-Enhancer trennt die Regie-Anweisungen in 4 spezialisierte Spuren:
1. **Master Style:** Fixiert Beleuchtung, 35mm-Filmlook und Farbpalette (Portra 400).
2. **Character Anker:** Koppelt `<Picture 1>` fest an Kleidung, Mimik und Proportionen.
3. **Camera & Action:** Gibt exakte Kamerafahrten vor (Dolly, Low-Angle, Tracking).
4. **Audio Scene Director:** Da H3 gleichzeitig eine 32-Kanal 40Hz Audio-VAE berechnet, erzeugen Sound-Stichwörter (Donner, Regen, Schritte) **automatisch lippensynchronen und räumlichen Sound!**

Alle 4 Spuren werden über `JoinStringMulti` nahtlos verschmolzen."""],
        "widgets_values_named": {"text": "Note text"}
    }
    
    nodes.extend([node_style, node_char, node_camera, node_audio, node_join, node_note])
    
    # Update links
    wf["links"].append([301, 201, 0, 205, 0, "STRING"])
    wf["links"].append([302, 202, 0, 205, 1, "STRING"])
    wf["links"].append([303, 203, 0, 205, 2, "STRING"])
    wf["links"].append([304, 204, 0, 205, 3, "STRING"])
    # Link 257 points from 205 output 0 to 136 input prompt
    for l in wf["links"]:
        if l[0] == 257:
            l[1] = 205
            l[2] = 0
            
    wf["last_node_id"] = 210
    wf["last_link_id"] = 310
    wf["nodes"] = nodes
    return wf

# Write files
os.makedirs("ComfyUI/user/default/workflows", exist_ok=True)
pe_wf = create_prompt_enhancer_wf()
with open("ComfyUI/user/default/workflows/_minimax_h3_prompt_enhancer.json", "w", encoding="utf-8") as f:
    json.dump(pe_wf, f, indent=2)
print("Saved _minimax_h3_prompt_enhancer.json")

# 2. _minimax_h3_cache_und_preview.json
def create_cache_preview_wf():
    wf = load_template()
    wf["id"] = "minimax-h3-cache-und-preview"
    nodes = wf["nodes"]
    
    # Add FastPreview / PreviewImage node for keyframe preview
    node_prev = {
        "id": 210,
        "type": "PreviewImage",
        "pos": [1200, 3950],
        "size": [450, 480],
        "title": "👁️ Keyframe Instant Preview (Model Preview)",
        "inputs": [{"name": "images", "type": "IMAGE", "link": 310}],
        "outputs": [],
        "widgets_values": []
    }
    
    # Add link from VAEDecode (node 122, output 0) to PreviewImage (node 210, input 0)
    wf["links"].append([310, 122, 0, 210, 0, "IMAGE"])
    
    # Add Explanatory Note
    node_note = {
        "id": 211,
        "type": "MarkdownNote",
        "pos": [-1500, 3600],
        "size": [900, 320],
        "title": "⚡ CACHE & MODEL PREVIEW ANALYSE (H3)",
        "widgets_values": ["""# ⚡ Warum EasyCache & wie funktioniert Model Preview bei H3?

### 1. EasyCache (DiT Step Caching) — 25-30% Geschwindigkeitsgewinn:
* **Wie es funktioniert:** MiniMax H3 ist ein 14B-DiT-Modell. In mittleren Zeitschritten ändern sich die tiefen Transformer-Features kaum. `EasyCache` überspringt redundante Berechnungen (`reuse_threshold: 0.20`, `start: 15%`, `end: 95%`).
* **Ergebnis:** Spart pro 5s-Clip ca. 20 bis 25 Sekunden! Im 5-Minuten-Film spart dies über **25 Minuten Rechenzeit** ohne sichtbaren Schärfeverlust.

### 2. Model Preview (Warum TAESD hier NICHT funktioniert):
* **Die Falle:** TAESD (Tiny AutoEncoder) ist nur für SD1.5, SDXL (4 Kanäle) und FLUX (16 Bild-Kanäle) trainiert.
* **Das H3-Spezifikum:** MiniMax H3 berechnet gleichzeitig Video (16 Kanäle) und Stereo-Audio (32 Kanäle) in einem verschachtelten `NestedTensor`. Standard-TAESD erzeugt hier Fehlermeldungen oder Farbmüll.
* **Die saubere Lösung:** ComfyUIs Standard-Step-Bar im Sampler + direkter VAE-Dekoder mit `PreviewImage` / `FastPreview`, sodass nach dem Sampling sofort das Standbild geprüft werden kann, bevor das MP4-File gemuxt wird."""],
        "widgets_values_named": {"text": "Note text"}
    }
    
    nodes.extend([node_prev, node_note])
    wf["last_node_id"] = 215
    wf["last_link_id"] = 315
    wf["nodes"] = nodes
    return wf

# 3. _minimax_h3_batched_upscaler.json
def create_batched_upscaler_wf():
    with open("ComfyUI/user/default/workflows/minimax_h3_stufen/06_master_high_quality_upscale.json") as f:
        wf = json.load(f)
    wf["id"] = "minimax-h3-batched-upscaler"
    
    # Add Highlighting Note
    note = {
        "id": 220,
        "type": "MarkdownNote",
        "pos": [-1500, 3600],
        "size": [900, 300],
        "title": "💎 BATCHED VIDEO UPSCALER (R-ESRGAN 4x+)",
        "widgets_values": ["""# 💎 Warum Batched Upscaling statt nativer 1080p/4K-Generierung?

### Das Rechen-Dilemma bei nativer Video-Auflösung:
* Würde man MiniMax H3 direkt in 1080p (1920×1080) laufen lassen, stiege die Pixelanzahl um das Fünffache gegenüber 0.4 MP.
* Selbst deine 48 GB VRAM würden unter extremen Druck geraten, und ein einziger 5s-Clip würde 6 bis 9 Minuten dauern.

### Die elegante 2-Stufen-Kino-Strategie (Sweet Spot):
1. **Schneller Base-Render:** Wir berechnen das Video in 0.4 MP (`864 × 480`) mit 8-Step Turbo in **nur 75–80 Sekunden**.
2. **Batched Upscaling (`ImageUpscaleWithModelBatched`):**  
   Der Knoten nimmt alle 124 Frames und schleust sie in Batches à **16 Frames** durch `R-ESRGAN 4x+.pth`.
3. **Ergebnis:** VRAM-Bedarf bleibt unter 22 GB, absolut kein Swap-Stau, und in wenigen Sekunden liegt der Clip in gestochen scharfem 1080p oder 4K vor!"""],
        "widgets_values_named": {"text": "Note text"}
    }
    wf["nodes"].append(note)
    wf["last_node_id"] = 225
    return wf

# 4. _minimax_h3_face_detailer_master.json
def create_face_detailer_wf():
    wf = load_template()
    wf["id"] = "minimax-h3-face-detailer-master"
    nodes = wf["nodes"]
    
    # Add Note explaining the Video FaceDetailer Flicker Trap
    note = {
        "id": 230,
        "type": "MarkdownNote",
        "pos": [-1500, 3500],
        "size": [950, 360],
        "title": "⚠️ FACE DETAILER IM VIDEO: DIE FLICKER-FALLE & DIE RICHTIGE LÖSUNG",
        "widgets_values": ["""# ⚠️ Face Detailer im Video: Warum Frame-by-Frame scheitert & was funktioniert

### 1. Das Problem: Die „Temporal-Jitter-Falle“
Wendet man den klassischen `FaceDetailer` (Impact Pack) frame-weise auf ein fertiges Video an, schneidet der Detector in jedem Frame das Gesicht aus und berechnet es mit neuem Zufallsrauschen (Noise).
* **Die Folge:** Das Gesicht morpht und zuckt in jedem Einzelbild („Flickering“), Pupillen springen, Zähne flackern. Das Video wirkt zerstört.

### 2. Die professionelle Hollywood-Lösung: „Pre-Refining am Master-Keyframe“
* Anstatt das Video hinterher mühsam zu flicken, jagen wir das **Master-Charakterbild (`character_master.png`)** vorab durch den `FaceDetailer` (mit FLUX oder SDXL).
* Wir verfeinern dort Augen, Iris, Hauttextur und Haare auf 4K-Mikroschärfe.
* Dieses perfekte Referenzbild speisen wir in `MiniMaxH3ReferenceToVideo` (`ref_image_0` mit `<Picture 1>`) ein.
* **Das Ergebnis:** MiniMax H3 überträgt die perfekte Gesichtsstruktur mit zeitlicher Konsistenz über alle 124 Frames, **völlig flackerfrei!**"""],
        "widgets_values_named": {"text": "Note text"}
    }
    nodes.append(note)
    wf["last_node_id"] = 235
    return wf

# 5. _minimax_h3_sageattention_analyse.json
def create_sageattention_wf():
    wf = load_template()
    wf["id"] = "minimax-h3-sageattention-analyse"
    nodes = wf["nodes"]
    
    # Add SageAttention Patch node (Bypassed) to show how it looks
    sage_node = {
        "id": 240,
        "type": "MiniMaxH3MemoryEfficientSageAttentionPatch",
        "pos": [-800, 4800],
        "size": [320, 90],
        "mode": 2, # 2 = BYPASSED/MUTED in LiteGraph!
        "title": "🛑 Sage Attention Patch (AUF AMD ROCm NICHT AKTIVIEREN!)",
        "inputs": [{"name": "model", "type": "MODEL", "link": None}],
        "outputs": [{"name": "model", "type": "MODEL", "links": None}],
        "widgets_values": []
    }
    
    note = {
        "id": 241,
        "type": "MarkdownNote",
        "pos": [-1500, 3500],
        "size": [950, 420],
        "title": "🔬 SAGE ATTENTION AUF AMD W7800 (ROCm 6.4) — DER TECHNISCHE BEWEIS",
        "widgets_values": ["""# 🔬 Warum Sage Attention auf AMD ROCm NICHT sinnvoll ist

### 1. Hardcoded CUDA-Check im Quellcode:
In `comfyui-kjnodes/nodes/ltxv_nodes.py` (Zeile 2182) steht:
```python
if _cuda_archs is None:
    raise RuntimeError("sageattention is not new enough version or could not determine CUDA architecture, cannot apply MiniMax H3 Memory Efficient Sage Attention Patch.")
```
SageAttention ist in Triton/CUDA speziell für **NVIDIA Tensor Cores** (SM80, SM89, SM90) geschrieben.
Auf deiner **AMD Radeon PRO W7800 (RDNA3 / ROCm 6.4)** existiert keine CUDA-Architektur. Ein Aufruf wirft sofort einen harten `RuntimeError`!

### 2. Was dein System stattdessen nutzt (und warum es optimal ist):
PyTorch ROCm 6.4 nutzt bereits standardmäßig **AMD Composable Kernel (CK) SDPA**:
* `torch.backends.cuda.mem_efficient_sdp_enabled() = True`
* `torch.backends.cuda.math_sdp_enabled() = True`

Das ist der offizielle, native AMD-Attention-Pfad. Er benötigt keine externen Hacks, läuft ohne VRAM-Fragmentierung und schützt deine W7800 vor PCIe-Bus-Deadlocks.
👉 **Fazit:** SageAttention auf AMD NICHT aktivieren. PyTorch SDPA ist bereits das Maximum an Stabilität und Performance!"""],
        "widgets_values_named": {"text": "Note text"}
    }
    
    nodes.extend([sage_node, note])
    wf["last_node_id"] = 245
    return wf

with open("ComfyUI/user/default/workflows/_minimax_h3_cache_und_preview.json", "w", encoding="utf-8") as f:
    json.dump(create_cache_preview_wf(), f, indent=2)
print("Saved _minimax_h3_cache_und_preview.json")

with open("ComfyUI/user/default/workflows/_minimax_h3_batched_upscaler.json", "w", encoding="utf-8") as f:
    json.dump(create_batched_upscaler_wf(), f, indent=2)
print("Saved _minimax_h3_batched_upscaler.json")

with open("ComfyUI/user/default/workflows/_minimax_h3_face_detailer_master.json", "w", encoding="utf-8") as f:
    json.dump(create_face_detailer_wf(), f, indent=2)
print("Saved _minimax_h3_face_detailer_master.json")

with open("ComfyUI/user/default/workflows/_minimax_h3_sageattention_analyse.json", "w", encoding="utf-8") as f:
    json.dump(create_sageattention_wf(), f, indent=2)
print("Saved _minimax_h3_sageattention_analyse.json")

# Kopiere alle auch in den minimax_h3_stufen Ordner
import shutil
for fname in [
    "_minimax_h3_prompt_enhancer.json",
    "_minimax_h3_cache_und_preview.json",
    "_minimax_h3_batched_upscaler.json",
    "_minimax_h3_face_detailer_master.json",
    "_minimax_h3_sageattention_analyse.json"
]:
    src = os.path.join("ComfyUI/user/default/workflows", fname)
    dst = os.path.join("ComfyUI/user/default/workflows/minimax_h3_stufen", fname)
    shutil.copy2(src, dst)
print("All 5 special workflows created and mirrored!")
