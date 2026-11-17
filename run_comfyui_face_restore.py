#!/usr/bin/env python3
"""
Führt lokal über die ComfyUI-Modelle (CodeFormer v0.1.0 + GFPGAN v1.4) die
KI-Gesichts- und Haar-Optimierung durch, baut daraus das optimierte Sonnenbild
sowie die 5 Zwischenbilder (0s, 5s, 10s, 15s, 20s) für Schritt 1.
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
sys.path.insert(0, str(REACTOR_DIR))

from nodes import RestoreFace

INPUT_DIR = COMFY_DIR / "input"
VW, VH = 720, 1280
FPS = 24
HEAD_SCALE_IN_SUN = 0.56
EDGE_FEATHER_PX = 16.0
RIM_GLOW_PX = 12.0


def pil_to_tensor(img: Image.Image) -> torch.Tensor:
    arr = np.array(img.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def tensor_to_pil(t: torch.Tensor) -> Image.Image:
    arr = np.clip(t.squeeze(0).cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def prepare_comfyui_restored_head() -> tuple[Image.Image, Image.Image, Image.Image]:
    """
    1. Lädt merko_mjezwoco.JPG
    2. Optimiert Gesicht & Haare lokal über ComfyUI RestoreFace (CodeFormer & GFPGAN)
    3. Stellt den kompletten Kopf mit sanftem Übergang zur Sonne frei
    """
    orig = Image.open(INPUT_DIR / "merko_mjezwoco.JPG").convert("RGB")
    mw, mh = orig.size

    # Zuerst auf 2.5x hochskalieren, damit ComfyUI RestoreFace maximale Auflösung hat
    scale_f = 2.5
    uw, uh = int(mw * scale_f), int(mh * scale_f)
    up_orig = orig.resize((uw, uh), Image.Resampling.LANCZOS)

    restorer = RestoreFace()
    t_in = pil_to_tensor(up_orig)

    # ComfyUI CodeFormer (w=0.55) für plastische, natürliche blonde Haarsträhnen & klare Augen
    (t_cf,) = restorer.execute(
        image=t_in,
        model="codeformer-v0.1.0.pth",
        visibility=0.92,
        codeformer_weight=0.55,
        facedetection="retinaface_resnet50",
    )
    img_cf = tensor_to_pil(t_cf)

    # ComfyUI GFPGAN v1.4 für seidige Haut & feine Details, 50/50 mit CodeFormer gemischt
    (t_gfp,) = restorer.execute(
        image=t_in,
        model="GFPGANv1.4.pth",
        visibility=0.92,
        codeformer_weight=0.55,
        facedetection="retinaface_resnet50",
    )
    img_gfp = tensor_to_pil(t_gfp)

    # Speichere das von ComfyUI KI-optimierte Porträt in ComfyUI/input/
    comfy_restored_portrait = Image.blend(img_cf, img_gfp, 0.45)

    # Sanfte Lichter-Kompression (Gamma 1.22 nur in den extrem hellen Spitzen > 215),
    # damit die von CodeFormer/GFPGAN erzeugten blonden Haarsträhnen einen warmen Naturblond-Ton haben
    arr = np.array(comfy_restored_portrait).astype(np.float32)
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    # Nur dort, wo g >= r - 2 (überbelichtetes Haar im Scan, nicht die rosige Haut)
    hair_zone = np.clip((arr[:, :, 1] - arr[:, :, 0] + 6.0) / 14.0, 0.0, 1.0) * np.clip((lum - 190.0) / 55.0, 0.0, 1.0)
    # Ziehe das kalte Grün/Blau in den überbelichteten Spitzen leicht zurück zu warmem Natur-Goldblond
    arr[:, :, 0] = np.clip(arr[:, :, 0] - hair_zone * 6.0, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] - hair_zone * 22.0, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] - hair_zone * 52.0, 0, 255)
    comfy_restored_portrait = Image.fromarray(arr.astype(np.uint8))
    comfy_restored_portrait.save(INPUT_DIR / "merko_mjezwoco_hd_clean.png", quality=95)

    # 2. Alpha-Maske auf Originalgröße berechnen und auf uw x uh hochskalieren
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

    # Auf uw x uh skalieren und Kontur glätten
    head_alpha_up = head_alpha.resize((uw, uh), Image.Resampling.BICUBIC)
    head_alpha_smooth = head_alpha_up.filter(ImageFilter.GaussianBlur(radius=9.0))
    head_alpha_round = head_alpha_smooth.point(
        lambda p: 0 if p < 70 else (255 if p > 185 else int(255 * ((p - 70.0) / 115.0) ** 1.2))
    )
    head_alpha_hd = head_alpha_round.filter(ImageFilter.GaussianBlur(radius=EDGE_FEATHER_PX))

    # Äußeren Saum an das warme Sonnengold angleichen (verhindert dunkle Studio-Ränder)
    head_rgb_hd = comfy_restored_portrait.copy()
    inner_core_hd = head_alpha_round.filter(ImageFilter.MinFilter(int(RIM_GLOW_PX * 1.5) | 1)).filter(
        ImageFilter.GaussianBlur(radius=RIM_GLOW_PX)
    )
    sun_gold_hd = Image.new("RGB", (uw, uh), (255, 226, 88))
    head_rgb_hd = Image.composite(head_rgb_hd, sun_gold_hd, inner_core_hd)

    # Im 640x640 Sonnen-Canvas zentrieren & um -11.5° aufrichten
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
    return full_head_rgba, img_cf, img_gfp


def warp_full_head(
    rgba_img: Image.Image,
    smile_level: float = 0.75,
    blink_level: float = 0.0,
    brow_lift: float = 0.45,
    gaze_x: float = 0.0,
    mouth_open: float = 0.20,
    head_tilt_deg: float = 0.0,
) -> Image.Image:
    S = rgba_img.size[0]
    k = S / 640.0
    grid_n = 24
    step = S / grid_n

    def get_source_uv(x: float, y: float):
        dx, dy = 0.0, 0.0
        for sign, mcx, mcy in [(-1.0, 268.0 * k, 498.0 * k), (1.0, 385.0 * k, 498.0 * k)]:
            dist2 = ((x - mcx) / (58.0 * k)) ** 2 + ((y - mcy) / (58.0 * k)) ** 2
            if dist2 < 4.0:
                w = math.exp(-dist2 * 1.15)
                dx += sign * 15.0 * k * smile_level * w
                dy += -19.0 * k * smile_level * w
        for sign, ccx, ccy in [(-1.0, 228.0 * k, 440.0 * k), (1.0, 425.0 * k, 440.0 * k)]:
            dist2 = ((x - ccx) / (72.0 * k)) ** 2 + ((y - ccy) / (64.0 * k)) ** 2
            if dist2 < 4.0:
                w = math.exp(-dist2 * 1.15)
                dx += sign * 5.5 * k * smile_level * w
                dy += -10.5 * k * smile_level * w
        dist_lip = ((x - 326.0 * k) / (64.0 * k)) ** 2 + ((y - 522.0 * k) / (40.0 * k)) ** 2
        if dist_lip < 4.0:
            w = math.exp(-dist_lip * 1.2)
            dy += 12.0 * k * mouth_open * w
        for ecx, ecy in [(265.0 * k, 372.0 * k), (395.0 * k, 372.0 * k)]:
            dist_eye = ((x - ecx) / (40.0 * k)) ** 2 + ((y - ecy) / (28.0 * k)) ** 2
            if dist_eye < 4.0:
                w = math.exp(-dist_eye * 1.35)
                if y < ecy + 12.0 * k:
                    dy += 22.0 * k * blink_level * w
                if y > ecy:
                    dy += -4.5 * k * max(0.0, smile_level) * w
                dist_iris = ((x - ecx) / (20.0 * k)) ** 2 + ((y - ecy) / (16.0 * k)) ** 2
                if dist_iris < 2.5:
                    wi = math.exp(-dist_iris * 1.6) * (1.0 - blink_level)
                    dx += 7.5 * k * gaze_x * wi
        for bcx, bcy in [(262.0 * k, 322.0 * k), (398.0 * k, 322.0 * k)]:
            dist_brow = ((x - bcx) / (52.0 * k)) ** 2 + ((y - bcy) / (32.0 * k)) ** 2
            if dist_brow < 4.0:
                w = math.exp(-dist_brow * 1.2)
                dy += -9.0 * k * brow_lift * w
        return (x - dx, y - dy)

    mesh = []
    for r in range(grid_n):
        for c in range(grid_n):
            x0, y0 = int(round(c * step)), int(round(r * step))
            x1, y1 = int(round((c + 1) * step)), int(round((r + 1) * step))
            u0, v0 = get_source_uv(x0, y0)
            u1, v1 = get_source_uv(x0, y1)
            u2, v2 = get_source_uv(x1, y1)
            u3, v3 = get_source_uv(x1, y0)
            mesh.append(((x0, y0, x1, y1), (u0, v0, u1, v1, u2, v2, u3, v3)))

    warped = rgba_img.transform((S, S), Image.Transform.MESH, mesh, resample=Image.Resampling.BILINEAR)
    if abs(head_tilt_deg) > 0.01:
        warped = warped.rotate(head_tilt_deg, resample=Image.Resampling.BICUBIC, center=(S * 0.5, S * 0.5))
    return warped


def prepare_hill_layers():
    f001 = Image.open(INPUT_DIR / "sonne_hill_mask_ref.png").convert("RGB")
    f095 = Image.open(INPUT_DIR / "sonne_hill_color_ref.png").convert("RGB")
    fw, fh = f001.size

    horizon_392 = []
    for x in range(fw):
        hy = 495
        for y in range(440, fh):
            r, g, b = f001.getpixel((x, y))
            if r < 85 and g < 75 and b < 60:
                hy = y
                break
        horizon_392.append(hy)

    horizon_smooth = []
    for x in range(fw):
        window = horizon_392[max(0, x - 6) : min(fw, x + 7)]
        horizon_smooth.append(sum(window) / len(window) + 16.0)

    hill_clean_392 = f095.copy()
    for x in range(fw):
        hy_int = int(math.ceil(horizon_smooth[x]))
        for y in range(0, hy_int + 6):
            src_y = min(fh - 1, hy_int + 10 + (hy_int - y) % 18)
            hill_clean_392.putpixel((x, y), f095.getpixel((x, src_y)))

    hill_bright = hill_clean_392.crop((0, 36, fw, fh)).resize((VW, VH), Image.Resampling.LANCZOS)
    hill_bright = ImageEnhance.Color(hill_bright).enhance(1.32)
    hill_bright = ImageEnhance.Brightness(hill_bright).enhance(1.16)
    hill_bright = ImageEnhance.Contrast(hill_bright).enhance(1.08)
    hill_bright = hill_bright.filter(ImageFilter.UnsharpMask(radius=2.0, percent=135, threshold=2))

    hill_offset_y = int(95 * (VH / 1920.0))
    hill_day = Image.new("RGB", (VW, VH))
    hill_day.paste(hill_bright.crop((0, 0, VW, VH - hill_offset_y)), (0, hill_offset_y))

    hill_dawn = ImageEnhance.Brightness(hill_day).enhance(0.28)
    hill_dawn = ImageEnhance.Color(hill_dawn).enhance(0.65)

    hill_mask = Image.new("L", (VW, VH), 0)
    draw_hm = ImageDraw.Draw(hill_mask)
    poly = []
    for x_v in range(VW):
        fx = (x_v / (VW - 1)) * (fw - 1)
        ix = int(fx)
        frac = fx - ix
        hy_392 = horizon_smooth[ix] * (1 - frac) + horizon_smooth[min(fw - 1, ix + 1)] * frac
        y_v = (hy_392 - 36.0) * (VH / (fh - 36.0)) + hill_offset_y
        poly.append((x_v, y_v))
    poly.append((VW, VH))
    poly.append((0, VH))
    draw_hm.polygon(poly, fill=255)
    hill_mask_soft = hill_mask.filter(ImageFilter.GaussianBlur(radius=4.0))
    return hill_dawn, hill_day, hill_mask_soft


def render_keyframe(sec: float, face_base_v: Image.Image, hill_dawn: Image.Image, hill_day: Image.Image, hill_mask_soft: Image.Image) -> Image.Image:
    f_idx = int(sec * FPS)
    sun_cx = VW // 2
    start_sun_y = int(1180 * (VH / 1280.0))
    end_sun_y = int(493 * (VH / 1280.0))

    if sec < 1.2:
        rise_p = 0.0
    elif sec < 14.5:
        u = (sec - 1.2) / (14.5 - 1.2)
        rise_p = 1.0 - math.pow(1.0 - u, 2.0)
    else:
        rise_p = 1.0

    hover_y = math.sin(sec * 2.2) * 4.5 if sec > 14.5 else 0.0
    hover_x = math.sin(sec * 1.4) * 3.5
    sun_cy = start_sun_y + (end_sun_y - start_sun_y) * rise_p + hover_y
    cur_sun_cx = sun_cx + hover_x

    sky_p = min(1.0, max(0.0, (sec - 0.5) / 10.5))
    hill_p = min(1.0, max(0.0, (sec - 1.5) / 9.0))
    beam_rot = f_idx * 0.005
    pulse = 1.0 + 0.028 * math.sin(f_idx * 0.14)

    if sec < 5.8:
        base_smile = -0.35 + 0.15 * math.sin(sec * 1.2)
        mouth_open = -0.42 + 0.08 * math.sin(sec * 2.0)
    elif sec < 8.2:
        su = (sec - 5.8) / (8.2 - 5.8)
        su_smooth = su * su * (3.0 - 2.0 * su)
        base_smile = -0.30 + (0.85 + 0.30) * su_smooth
        mouth_open = -0.40 + 0.65 * su_smooth
    else:
        base_smile = 0.85 + 0.12 * math.sin((sec - 8.2) * 3.8)
        mouth_open = 0.20 + 0.24 * abs(math.sin((sec - 8.0) * 4.2)) * math.cos((sec - 8.0) * 1.5)

    gaze_x = 0.55 * math.sin(sec * 1.6) if sec < 7.0 else 0.22 * math.sin(sec * 1.1)
    brow_lift = -0.15 if sec < 6.0 else min(0.60, (sec - 6.0) * 0.35) + 0.15 * math.sin(sec * 3.0)
    head_tilt_deg = 3.0 * math.sin(sec * 1.35) + (1.8 * math.cos(sec * 2.7) if sec > 7.8 else 0.0)

    warped_face = warp_full_head(
        face_base_v,
        smile_level=base_smile,
        blink_level=0.0,
        brow_lift=brow_lift,
        gaze_x=gaze_x,
        mouth_open=mouth_open,
        head_tilt_deg=head_tilt_deg,
    )

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, VW, VH)
    ctx = cairo.Context(surface)

    sky_grad = cairo.LinearGradient(0, 0, 0, int(1060 * (VH / 1280.0)))
    sky_grad.add_color_stop_rgb(0.0, 0.25 * (1 - sky_p) + 0.34 * sky_p, 0.18 * (1 - sky_p) + 0.50 * sky_p, 0.16 * (1 - sky_p) + 0.65 * sky_p)
    sky_grad.add_color_stop_rgb(0.42, 0.58 * (1 - sky_p) + 0.55 * sky_p, 0.40 * (1 - sky_p) + 0.72 * sky_p, 0.30 * (1 - sky_p) + 0.83 * sky_p)
    sky_grad.add_color_stop_rgb(0.78, 0.88 * (1 - sky_p) + 0.85 * sky_p, 0.65 * (1 - sky_p) + 0.90 * sky_p, 0.42 * (1 - sky_p) + 0.86 * sky_p)
    sky_grad.add_color_stop_rgb(1.0, 1.0, 0.91, 0.62)
    ctx.set_source(sky_grad)
    ctx.paint()

    num_long_beams = 16
    beam_alpha = 0.18 + 0.38 * sky_p
    for i in range(num_long_beams):
        angle1 = beam_rot * 0.5 + (2 * math.pi * i) / num_long_beams - 0.068
        angle2 = angle1 + 0.136
        beam_grad = cairo.RadialGradient(cur_sun_cx, sun_cy, 100, cur_sun_cx, sun_cy, 920)
        beam_grad.add_color_stop_rgba(0.0, 1.0, 0.97, 0.78, beam_alpha)
        beam_grad.add_color_stop_rgba(0.5, 1.0, 0.94, 0.68, beam_alpha * 0.55)
        beam_grad.add_color_stop_rgba(1.0, 1.0, 0.92, 0.58, 0.0)
        ctx.set_source(beam_grad)
        ctx.move_to(cur_sun_cx, sun_cy)
        ctx.line_to(cur_sun_cx + math.cos(angle1) * 1100, sun_cy + math.sin(angle1) * 1100)
        ctx.line_to(cur_sun_cx + math.cos(angle2) * 1100, sun_cy + math.sin(angle2) * 1100)
        ctx.close_path()
        ctx.fill()

    halo_r = 420 * pulse
    halo_grad = cairo.RadialGradient(cur_sun_cx, sun_cy, 130, cur_sun_cx, sun_cy, halo_r)
    halo_grad.add_color_stop_rgba(0.0, 1.0, 0.95, 0.52, 0.95)
    halo_grad.add_color_stop_rgba(0.55, 1.0, 0.90, 0.38, 0.60)
    halo_grad.add_color_stop_rgba(0.85, 1.0, 0.85, 0.28, 0.20)
    halo_grad.add_color_stop_rgba(1.0, 1.0, 0.82, 0.22, 0.0)
    ctx.set_source(halo_grad)
    ctx.arc(cur_sun_cx, sun_cy, halo_r, 0, 2 * math.pi)
    ctx.fill()

    def draw_spikes_v(n_spikes, r_in, r_out, rot_off, a_scale):
        ctx.move_to(cur_sun_cx + math.cos(rot_off) * r_out, sun_cy + math.sin(rot_off) * r_out)
        for i in range(1, n_spikes * 2 + 1):
            ang = rot_off + (math.pi * i) / n_spikes
            r = r_out + (13 if (i // 2) % 2 == 0 else -8) if i % 2 == 0 else r_in
            ctx.line_to(cur_sun_cx + math.cos(ang) * r, sun_cy + math.sin(ang) * r)
        ctx.close_path()
        sp_grad = cairo.RadialGradient(cur_sun_cx, sun_cy, r_in * 0.7, cur_sun_cx, sun_cy, r_out + 18)
        sp_grad.add_color_stop_rgba(0.0, 1.0, 0.86, 0.20, 1.0 * a_scale)
        sp_grad.add_color_stop_rgba(0.62, 1.0, 0.92, 0.42, 0.96 * a_scale)
        sp_grad.add_color_stop_rgba(0.90, 1.0, 0.97, 0.74, 0.82 * a_scale)
        sp_grad.add_color_stop_rgba(1.0, 1.0, 0.99, 0.88, 0.0)
        ctx.set_source(sp_grad)
        ctx.fill()

    draw_spikes_v(18, 203, 343 * pulse, -beam_rot * 0.6 + math.pi / 18, 0.65)
    draw_spikes_v(18, 200, 330 * pulse, beam_rot, 0.98)

    core_grad = cairo.RadialGradient(cur_sun_cx, sun_cy, 8, cur_sun_cx, sun_cy, 225)
    core_grad.add_color_stop_rgba(0.0, 1.0, 0.91, 0.36, 1.0)
    core_grad.add_color_stop_rgba(0.65, 1.0, 0.84, 0.22, 1.0)
    core_grad.add_color_stop_rgba(0.90, 1.0, 0.86, 0.28, 0.95)
    core_grad.add_color_stop_rgba(1.0, 1.0, 0.92, 0.45, 0.0)
    ctx.set_source(core_grad)
    ctx.arc(cur_sun_cx, sun_cy, 225, 0, 2 * math.pi)
    ctx.fill()

    buf = surface.get_data()
    frame_img = Image.frombuffer("RGBA", (VW, VH), buf, "raw", "BGRA", 0, 1).convert("RGB")

    face_size_v = face_base_v.size[0]
    px = int(round(cur_sun_cx - face_size_v // 2))
    py = int(round(sun_cy - face_size_v // 2))
    frame_img.paste(warped_face, (px, py), warped_face)

    cur_hill = Image.blend(hill_dawn, hill_day, hill_p)
    return Image.composite(cur_hill, frame_img, hill_mask_soft)


def main():
    print("Starte lokale ComfyUI-Restaurierung (CodeFormer + GFPGAN) für merko_mjezwoco.JPG...")
    full_head_rgba_640, _, _ = prepare_comfyui_restored_head()
    full_head_rgba_640.save(INPUT_DIR / "merko_comfyui_head_640.png")

    bg_result1 = Image.open(INPUT_DIR / "option2_1_sonne_background_hd.png").convert("RGB")
    smiling_still_640 = warp_full_head(full_head_rgba_640, smile_level=0.55, brow_lift=0.35, mouth_open=0.12)
    res2_hd = bg_result1.copy()
    res2_hd.paste(smiling_still_640, (1080 // 2 - 320, 740 - 320), smiling_still_640)
    res2_hd.save(INPUT_DIR / "option2_2_sonne_mit_gesicht_hd.png", quality=95)

    comp = Image.new("RGB", (1080 * 2 + 20, 1920), (20, 20, 20))
    comp.paste(bg_result1, (0, 0))
    comp.paste(res2_hd, (1080 + 20, 0))
    comp.resize((1090, 960), Image.Resampling.LANCZOS).save(
        INPUT_DIR / "option2_beide_ergebnisse_vergleich.jpg", quality=92
    )
    print("Fertig! ComfyUI-optimiertes Gesicht gespeichert unter: ComfyUI/input/option2_2_sonne_mit_gesicht_hd.png")


if __name__ == "__main__":
    main()
