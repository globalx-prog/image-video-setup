#!/usr/bin/env python3
"""
Führt lokal einen ComfyUI SDXL-Inpainting-Workflow (Juggernaut-XL_v9_RunDiffusionPhoto.safetensors)
nur auf der überbelichteten Haar-Krone von merko_mjezwoco_hd_clean.png aus, um echte,
fotorealistische blonde Kinderhaar-Strähnen zu generieren, und kombiniert sie mit dem
CodeFormer/GFPGAN-optimierten Originalgesicht.
"""
import math
import sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

COMFY_DIR = Path("/home/clemi/Projekte/LLM/image-video-setup/ComfyUI")
REACTOR_DIR = COMFY_DIR / "custom_nodes" / "comfyui-reactor-node"
sys.path.insert(0, str(COMFY_DIR))
import nodes as comfy_nodes

sys.path.insert(0, str(REACTOR_DIR))
import importlib.util
spec = importlib.util.spec_from_file_location("reactor_nodes", str(REACTOR_DIR / "nodes.py"))
reactor_nodes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reactor_nodes)
RestoreFace = reactor_nodes.RestoreFace

INPUT_DIR = COMFY_DIR / "input"
HEAD_SCALE_IN_SUN = 0.56
EDGE_FEATHER_PX = 16.0
RIM_GLOW_PX = 12.0


def pil_to_tensor(img: Image.Image) -> torch.Tensor:
    arr = np.array(img.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def tensor_to_pil(t: torch.Tensor) -> Image.Image:
    arr = np.clip(t.squeeze(0).cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def run_comfyui_hair_and_face_workflow():
    orig = Image.open(INPUT_DIR / "merko_mjezwoco.JPG").convert("RGB")
    mw, mh = orig.size

    # 1. Auf 1024x1024 skalieren (optimale SDXL Juggernaut-XL Auflösung)
    W, H = 960, 1024
    up_orig = orig.resize((W, H), Image.Resampling.LANCZOS)

    # 2. ComfyUI RestoreFace (CodeFormer + GFPGAN) für das perfekte Originalgesicht
    restorer = RestoreFace()
    t_in = pil_to_tensor(up_orig)
    (t_cf,) = restorer.execute(
        image=t_in,
        model="codeformer-v0.1.0.pth",
        visibility=0.92,
        codeformer_weight=0.55,
        facedetection="retinaface_resnet50",
    )
    (t_gfp,) = restorer.execute(
        image=t_in,
        model="GFPGANv1.4.pth",
        visibility=0.92,
        codeformer_weight=0.55,
        facedetection="retinaface_resnet50",
    )
    restored_face_img = Image.blend(tensor_to_pil(t_cf), tensor_to_pil(t_gfp), 0.45)

    # 3. Vor-Tönung des ausgebrannten grünstichigen Haarbereichs auf ein neutrales, warmes Blond als Init-Image für SDXL,
    #    damit Juggernaut-XL bei denoise=0.42 echte blonde Haarsträhnen statt Grünstich-Weiß erzeugt
    arr = np.array(restored_face_img).astype(np.float32)
    hair_mask_np = np.zeros((H, W), dtype=np.float32)
    for y in range(int(H * 0.54)):
        yw = 1.0 if y < int(H * 0.36) else max(0.0, (H * 0.54 - y) / (H * 0.18))
        for x in range(W):
            r, g, b = arr[y, x]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            # Überstrahltes Haar hat hohes lum (>175) und g >= r - 6
            if lum > 170 and (g >= r - 8):
                # Nicht in die Stirnhaut (unten Mitte) eingreifen
                in_forehead_skin = ((x - W * 0.52) / (W * 0.23)) ** 2 + ((y - H * 0.48) / (H * 0.12)) ** 2 < 1.0
                if not in_forehead_skin:
                    hm = yw * min(1.0, (lum - 170.0) / 50.0)
                    hair_mask_np[y, x] = hm
                    # Neutrale, warme Naturblond-Basis für SDXL img2img
                    arr[y, x, 0] = r * (1 - hm * 0.65) + 228.0 * (hm * 0.65)
                    arr[y, x, 1] = g * (1 - hm * 0.65) + 196.0 * (hm * 0.65)
                    arr[y, x, 2] = b * (1 - hm * 0.65) + 142.0 * (hm * 0.65)

    init_for_sdxl = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    hair_mask_pil = Image.fromarray(np.clip(hair_mask_np * 255.0, 0, 255).astype(np.uint8))
    hair_mask_pil = hair_mask_pil.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(radius=18.0))

    # 4. ComfyUI CheckpointLoaderSimple -> Juggernaut-XL_v9_RunDiffusionPhoto.safetensors
    print("Lade ComfyUI Checkpoint: Juggernaut-XL_v9_RunDiffusionPhoto.safetensors...")
    ckpt_loader = comfy_nodes.CheckpointLoaderSimple()
    model, clip, vae = ckpt_loader.load_checkpoint("Juggernaut-XL_v9_RunDiffusionPhoto.safetensors")

    pos_prompt = (
        "closeup studio portrait of a cute happy smiling young toddler boy with natural soft golden blonde hair, "
        "fine realistic hair strands, soft natural hair texture, warm lighting, photorealistic, 8k, detailed hair"
    )
    neg_prompt = (
        "overexposed white hair, glowing green hair, neon yellow, bald, plastic, Hat, cap, deformed, "
        "blurry, harsh lines, striped pattern"
    )

    clip_enc = comfy_nodes.CLIPTextEncode()
    (cond_pos,) = clip_enc.encode(clip, pos_prompt)
    (cond_neg,) = clip_enc.encode(clip, neg_prompt)

    vae_enc = comfy_nodes.VAEEncode()
    (latent,) = vae_enc.encode(vae, pil_to_tensor(init_for_sdxl))

    # SetLatentNoiseMask auf die Haarmaske beschränken, damit das Gesicht zu 100% original bleibt!
    mask_tensor = torch.from_numpy(np.array(hair_mask_pil).astype(np.float32) / 255.0).unsqueeze(0)
    set_mask = comfy_nodes.SetLatentNoiseMask()
    (latent_masked,) = set_mask.set_mask(latent, mask_tensor)

    ksampler = comfy_nodes.KSampler()
    vae_dec = comfy_nodes.VAEDecode()

    results = []
    for denoise_val, seed_val, tag in [(0.42, 42001, "dezent_blond"), (0.54, 42007, "strukturiert_blond")]:
        print(f"Starte ComfyUI KSampler für Haar-Restaurierung (denoise={denoise_val})...")
        (samples,) = ksampler.sample(
            model=model,
            seed=seed_val,
            steps=22,
            cfg=5.5,
            sampler_name="dpmpp_2m",
            scheduler="karras",
            positive=cond_pos,
            negative=cond_neg,
            latent_image=latent_masked,
            denoise=denoise_val,
        )
        (decoded,) = vae_dec.decode(vae, samples)
        sdxl_img = tensor_to_pil(decoded)
        # Mische über die weiche Haarmaske ausschließlich die neu generierten Haare auf das restaurierte Originalgesicht
        combined = Image.composite(sdxl_img, restored_face_img, hair_mask_pil)
        combined_orig_res = combined.resize((int(mw * 2.5), int(mh * 2.5)), Image.Resampling.LANCZOS)
        combined_orig_res.save(INPUT_DIR / f"merko_comfyui_{tag}.png", quality=95)
        results.append((tag, combined_orig_res))

    return results


def build_sun_head(comfy_portrait_hd: Image.Image) -> Image.Image:
    orig = Image.open(INPUT_DIR / "merko_mjezwoco.JPG").convert("RGB")
    mw, mh = orig.size
    uw, uh = comfy_portrait_hd.size

    head_alpha = Image.new("L", (mw, mh), 0)
    for y in range(mh):
        for x in range(mw):
            r, g, b = orig.getpixel((x, y))
            l_val = 0.299 * r + 0.587 * g + 0.114 * b
            warmth = r - g

            in_core = math.sqrt(((x - 210.0) / 86.0) ** 2 + ((y - 262.0) / 118.0) ** 2) < 0.95
            in_chin_core = math.sqrt(((x - 228.0) / 56.0) ** 2 + ((y - 365.0) / 42.0) ** 2) < 0.95
            if in_core or in_chin_core:
                head_alpha.putpixel((x, y), 255)
                continue

            if y <= 290:
                if l_val < 52:
                    head_alpha.putpixel((x, y), 0)
                elif l_val < 100:
                    head_alpha.putpixel((x, y), int(255 * (l_val - 52.0) / 48.0))
                else:
                    head_alpha.putpixel((x, y), 255)
            else:
                if l_val < 85 or warmth < 7:
                    head_alpha.putpixel((x, y), 0)
                elif warmth < 14:
                    a_w = (warmth - 7.0) / 7.0
                    a_l = min(1.0, (l_val - 85.0) / 35.0)
                    head_alpha.putpixel((x, y), int(255 * a_w * a_l))
                else:
                    head_alpha.putpixel((x, y), 255)

    head_alpha = head_alpha.filter(ImageFilter.MedianFilter(size=7)).filter(ImageFilter.MinFilter(5))
    head_alpha_up = head_alpha.resize((uw, uh), Image.Resampling.BICUBIC)
    head_alpha_smooth = head_alpha_up.filter(ImageFilter.GaussianBlur(radius=9.0))
    head_alpha_round = head_alpha_smooth.point(
        lambda p: 0 if p < 70 else (255 if p > 185 else int(255 * ((p - 70.0) / 115.0) ** 1.2))
    )
    head_alpha_hd = head_alpha_round.filter(ImageFilter.GaussianBlur(radius=EDGE_FEATHER_PX))

    head_rgb_hd = comfy_portrait_hd.copy()
    inner_core_hd = head_alpha_round.filter(ImageFilter.MinFilter(int(RIM_GLOW_PX * 1.5) | 1)).filter(
        ImageFilter.GaussianBlur(radius=RIM_GLOW_PX)
    )
    sun_gold_hd = Image.new("RGB", (uw, uh), (255, 226, 88))
    head_rgb_hd = Image.composite(head_rgb_hd, sun_gold_hd, inner_core_hd)

    canvas_s = 640
    canvas_rgb = Image.new("RGB", (canvas_s, canvas_s), (255, 224, 82))
    canvas_a = Image.new("L", (canvas_s, canvas_s), 0)

    fw_fit, fh_fit = int(uw * HEAD_SCALE_IN_SUN), int(uh * HEAD_SCALE_IN_SUN)
    head_fit_rgb = head_rgb_hd.resize((fw_fit, fh_fit), Image.Resampling.LANCZOS)
    head_fit_a = head_alpha_hd.resize((fw_fit, fh_fit), Image.Resampling.LANCZOS)

    ox = (canvas_s - fw_fit) // 2 - 6
    oy = (canvas_s - fh_fit) // 2 + 6
    canvas_rgb.paste(head_fit_rgb, (ox, oy))
    canvas_a.paste(head_fit_a, (ox, oy))

    rot_deg = -11.5
    canvas_rgb = canvas_rgb.rotate(rot_deg, resample=Image.Resampling.BICUBIC, center=(canvas_s // 2, canvas_s // 2))
    canvas_a = canvas_a.rotate(rot_deg, resample=Image.Resampling.BICUBIC, center=(canvas_s // 2, canvas_s // 2))

    full_head_rgba = canvas_rgb.copy()
    full_head_rgba.putalpha(canvas_a)
    return full_head_rgba


def main():
    results = run_comfyui_hair_and_face_workflow()
    bg_result1 = Image.open(INPUT_DIR / "option2_1_sonne_background_hd.png").convert("RGB")

    # Importiere warp_full_head aus run_comfyui_face_restore
    from run_comfyui_face_restore import warp_full_head

    crops = []
    for tag, portrait_hd in results:
        head_640 = build_sun_head(portrait_hd)
        smiling_640 = warp_full_head(head_640, smile_level=0.55, brow_lift=0.35, mouth_open=0.12)
        sun_full = bg_result1.copy()
        sun_full.paste(smiling_640, (1080 // 2 - 320, 740 - 320), smiling_640)
        sun_full.save(INPUT_DIR / f"option2_2_sonne_{tag}.png", quality=95)
        if tag == "strukturiert_blond":
            head_640.save(INPUT_DIR / "merko_comfyui_head_640.png")
            sun_full.save(INPUT_DIR / "option2_2_sonne_mit_gesicht_hd.png", quality=95)
            comp2 = Image.new("RGB", (1080 * 2 + 20, 1920), (20, 20, 20))
            comp2.paste(bg_result1, (0, 0))
            comp2.paste(sun_full, (1080 + 20, 0))
            comp2.resize((1090, 960), Image.Resampling.LANCZOS).save(
                INPUT_DIR / "option2_beide_ergebnisse_vergleich.jpg", quality=92
            )
        crops.append((tag, sun_full.crop((200, 400, 880, 1080)).resize((460, 460), Image.Resampling.LANCZOS)))

    grid = Image.new("RGB", (460 * 2 + 12, 500), (24, 24, 28))
    draw = ImageDraw.Draw(grid)
    for i, (tag, c_im) in enumerate(crops):
        x0 = i * (460 + 12)
        grid.paste(c_im, (x0, 36))
        draw.text((x0 + 16, 10), f"ComfyUI Juggernaut-XL + CodeFormer ({tag})", fill=(255, 230, 120))
    grid.save(INPUT_DIR / "comfyui_haar_inpaint_vergleich.jpg", quality=94)
    print("Fertig! ComfyUI Haar- & Gesichts-Optimierung abgeschlossen.")


if __name__ == "__main__":
    main()
