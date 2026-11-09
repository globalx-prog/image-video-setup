import json
import os
import shutil

# We load 06_master_high_quality_upscale.json which already has:
# Models, Turbo Switch, EasyCache, Sampler, VAE Decode, VAE Audio Decode,
# UpscaleModelLoader, ImageUpscaleWithModelBatched, CreateVideo, VRAMCleanup, SaveVideo.
with open("ComfyUI/user/default/workflows/minimax_h3_stufen/06_master_high_quality_upscale.json") as f:
    wf = json.load(f)

wf["id"] = "minimax-h3-master-all-in-one"
nodes = wf["nodes"]

# 1. Replace the single prompt node (node 138) with our 4-track Prompt Enhancer
nodes = [n for n in nodes if n["id"] != 138]

node_style = {
    "id": 201,
    "type": "StringConstantMultiline",
    "pos": [-1500, 3900],
    "size": [400, 150],
    "title": "🎨 1. Master Style (Visual Continuity)",
    "inputs": [],
    "outputs": [{"name": "string", "type": "STRING", "links": [301]}],
    "widgets_values": ["cinematic 35mm anamorphic film, golden hour dusk lighting, subtle volumetric haze, Kodak Portra 400 color grading, photorealistic, 8k"],
    "widgets_values_named": {"string": "cinematic 35mm anamorphic film, golden hour dusk lighting, subtle volumetric haze, Kodak Portra 400 color grading, photorealistic, 8k"}
}

node_char = {
    "id": 202,
    "type": "StringConstantMultiline",
    "pos": [-1500, 4080],
    "size": [400, 150],
    "title": "🐭 2. Character Anker (<Picture 1>)",
    "inputs": [],
    "outputs": [{"name": "string", "type": "STRING", "links": [302]}],
    "widgets_values": ["<Picture 1> the sharp mouse detective wearing a detailed brown trenchcoat and fedora hat, resolute expression"],
    "widgets_values_named": {"string": "<Picture 1> the sharp mouse detective wearing a detailed brown trenchcoat and fedora hat, resolute expression"}
}

node_camera = {
    "id": 203,
    "type": "StringConstantMultiline",
    "pos": [-1500, 4260],
    "size": [400, 150],
    "title": "🎥 3. Camera Movement & Action",
    "inputs": [],
    "outputs": [{"name": "string", "type": "STRING", "links": [303]}],
    "widgets_values": ["low-angle tracking dolly shot forward, walking briskly along the wet asphalt alley, neon signs reflecting in puddles"],
    "widgets_values_named": {"string": "low-angle tracking dolly shot forward, walking briskly along the wet asphalt alley, neon signs reflecting in puddles"}
}

node_audio = {
    "id": 204,
    "type": "StringConstantMultiline",
    "pos": [-1500, 4440],
    "size": [400, 150],
    "title": "🔊 4. Audio Scene Director (Synchroner Ton)",
    "inputs": [],
    "outputs": [{"name": "string", "type": "STRING", "links": [304]}],
    "widgets_values": ["heavy raindrops splashing on pavement, soft rumble of distant thunder, rhythmic trenchcoat fabric rustling, quiet footsteps"],
    "widgets_values_named": {"string": "heavy raindrops splashing on pavement, soft rumble of distant thunder, rhythmic trenchcoat fabric rustling, quiet footsteps"}
}

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

# 2. Add Instant Keyframe Preview Node
node_prev = {
    "id": 210,
    "type": "PreviewImage",
    "pos": [450, 4400],
    "size": [420, 420],
    "title": "👁️ Keyframe Instant Preview (Model Preview)",
    "inputs": [{"name": "images", "type": "IMAGE", "link": 310}],
    "outputs": [],
    "widgets_values": []
}

# 3. Add Master Banner Note
node_master_note = {
    "id": 250,
    "type": "MarkdownNote",
    "pos": [-1500, 3450],
    "size": [950, 400],
    "title": "👑 MASTER ALL-IN-ONE WORKFLOW (MINIMAX H3 KINO-PIPELINE)",
    "widgets_values": ["""# 👑 Master All-in-One: Alle Profi-Funktionen in einer Pipeline!

Dieser Workflow vereint alle sinnvollen Werkzeuge in einer perfekten Signalkette:

```
[1. Master-Charakterbild] ──┐
                            ├─► [3. MiniMax H3 Ref2V] ──► [4. Instant Preview]
[2. 4-Spur Prompt Enhancer] ─┘      (EasyCache + Turbo)            │
                                                                   ▼
                                                         [5. R-ESRGAN Upscaler] ──► [6. 1080p Video]
```

### Die aktiven Features im Überblick:
1. **4-Spur Prompt Enhancer:** Teilt den Prompt in Stil, Figur, Kamera und Audio auf.
2. **Charakter-Konsistenz:** Bindet Gesicht und Kleidung über `<Picture 1>` und `ref_image_0`.
3. **EasyCache:** Beschleunigt das Sampling um 20-30% ohne Schärfeverlust.
4. **Instant Preview:** Sofortige Bildvorschau des ersten dekodierten Frames.
5. **Batched Upscaler:** Skaliert die 124 Frames in 16er-Batches mit `R-ESRGAN 4x+` auf 1080p hoch (kein VRAM-Spike!).
6. **VRAMCleanup:** Gibt nach dem Speichern allen GPU- und RAM-Cache frei.

*(Hinweis zu SageAttention: Deaktiviert, da SageAttention nur für NVIDIA-Karten gebaut ist. PyTorch nutzt hier automatisch AMDs natives Composable-Kernel SDPA!)*"""],
    "widgets_values_named": {"text": "Note text"}
}

nodes.extend([node_style, node_char, node_camera, node_audio, node_join, node_prev, node_master_note])

# Fix / add links
wf["links"].append([301, 201, 0, 205, 0, "STRING"])
wf["links"].append([302, 202, 0, 205, 1, "STRING"])
wf["links"].append([303, 203, 0, 205, 2, "STRING"])
wf["links"].append([304, 204, 0, 205, 3, "STRING"])
wf["links"].append([310, 122, 0, 210, 0, "IMAGE"]) # link from VAEDecode (122) to PreviewImage (210)

# Connect JoinStringMulti (205) output 0 to node 136 (MiniMaxH3ReferenceToVideo) input prompt
for l in wf["links"]:
    if l[0] == 257:
        l[1] = 205
        l[2] = 0

wf["last_node_id"] = 260
wf["last_link_id"] = 320
wf["nodes"] = nodes

out_path_1 = "ComfyUI/user/default/workflows/_minimax_h3_master_all_in_one.json"
out_path_2 = "ComfyUI/user/default/workflows/minimax_h3_stufen/_minimax_h3_master_all_in_one.json"

with open(out_path_1, "w", encoding="utf-8") as f:
    json.dump(wf, f, indent=2)

shutil.copy2(out_path_1, out_path_2)
print("Successfully generated _minimax_h3_master_all_in_one.json in both locations!")
