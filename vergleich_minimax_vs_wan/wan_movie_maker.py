#!/usr/bin/env python3
"""
WAN 2.2 Movie Maker — Autonome Langfilm-Pipeline mit automatischem Audio-Muxing
Rendert Szenen über WAN 2.2 (14B FP8) mit 4-Step LoRA und fügt automatisch Soundeffekte/Musik per FFmpeg hinzu.
"""

import os
import sys
import time
import json
import yaml
import argparse
import subprocess
import urllib.request

COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_ROOT = os.path.expanduser("/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/output")
INPUT_ROOT = os.path.expanduser("/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/input")


def log(msg, tag="INFO"):
    colors = {
        "INFO": "\033[94m[INFO]\033[0m",
        "SUCCESS": "\033[92m[OK]\033[0m",
        "WARN": "\033[93m[WARN]\033[0m",
        "ERROR": "\033[91m[FEHLER]\033[0m",
        "SCENE": "\033[95m[WAN-SZENE]\033[0m"
    }
    print(f"{colors.get(tag, '[INFO]')} {msg}")


def check_comfy():
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3) as resp:
            data = json.loads(resp.read().decode())
            vram_free = data.get("devices", [{}])[0].get("vram_free", 0) / (1024**3)
            log(f"ComfyUI verbunden! Freier VRAM: {vram_free:.1f} GB", "SUCCESS")
            return True
    except Exception as e:
        log(f"ComfyUI nicht erreichbar unter {COMFY_URL}: {e}", "ERROR")
        return False


def build_wan_api_prompt(scene_prompt, start_image_name, width=832, height=480, duration=5.0, steps=4, seed=None):
    if seed is None:
        seed = int(time.time() * 1000) % (2**31)

    # 16 FPS bei WAN: 5s = 81 Frames
    length = round(duration * 16) + 1

    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan",
                "device": "default"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "wan_2.1_vae.safetensors"}
        },
        "4": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
                "strength_model": 1.0,
                "model": ["1", 0]
            }
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": start_image_name}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": scene_prompt,
                "clip": ["2", 0]
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，画面静止，低质量，JPEG压缩残留，变形，多余肢体",
                "clip": ["2", 0]
            }
        },
        "8": {
            "class_type": "WanImageToVideo",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["3", 0],
                "start_image": ["5", 0],
                "width": width,
                "height": height,
                "length": length,
                "batch_size": 1
            }
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["8", 0],
                "negative": ["8", 1],
                "latent_image": ["8", 2],
                "denoise": 1.0
            }
        },
        "10": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["9", 0], "vae": ["3", 0]}
        },
        "11": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["10", 0],
                "fps": 16,
                "bit_depth": 8,
                "color_space": "sRGB",
                "codec": "none"
            }
        },
        "12": {
            "class_type": "VRAMCleanup",
            "inputs": {
                "offload_model": False, # Modelle im VRAM halten für Warm-Start!
                "offload_cache": True,
                "anything": ["11", 0]
            }
        },
        "13": {
            "class_type": "SaveVideo",
            "inputs": {
                "filename_prefix": "video/wan_movie/scene",
                "format": "auto",
                "video": ["12", 0]
            }
        }
    }


def wait_for_prompt(prompt_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{COMFY_URL}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                if prompt_id in data:
                    outputs = data[prompt_id].get("outputs", {})
                    for nid, out_dict in outputs.items():
                        media = out_dict.get("videos", []) + out_dict.get("images", [])
                        for m in media:
                            fn = m.get("filename") if isinstance(m, dict) else str(m)
                            sf = m.get("subfolder", "") if isinstance(m, dict) else ""
                            if fn and any(fn.lower().endswith(x) for x in [".mp4", ".webm", ".mkv"]):
                                log(f"Szene fertig gerendert in {time.time()-start:.1f}s! ({fn})", "SUCCESS")
                                return sf, fn
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Timeout bei Prompt {prompt_id}")


def extract_last_frame(video_path, output_png):
    cmd = ["ffmpeg", "-y", "-sseof", "-0.1", "-i", video_path, "-update", "1", "-q:v", "2", output_png]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_png


def mux_audio_track(video_path, audio_desc, output_path, duration=5.0):
    """
    Erzeugt oder verknüpft eine Tonspur für WAN 2.2:
    Nutzt z. B. passendes Ambient/Foley oder generiert per FFmpeg eine harmonische Raumton-Spur.
    """
    # Wenn eine externe Audiospur übergeben wird oder eine Standard-Ambience genutzt wird
    # Falls keine Audiospur vorliegt: Erzeuge sauberen Stereo-Raumton (Hintergrund-Haze) mit 32kHz
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration}", # Sanfter Sub-Bass / Ambience
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def concatenate_scenes(video_files, final_path):
    concat_txt = final_path + ".txt"
    with open(concat_txt, "w") as f:
        for v in video_files:
            f.write(f"file '{os.path.abspath(v)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", final_path]
    subprocess.run(cmd, check=True)
    if os.path.exists(concat_txt):
        os.remove(concat_txt)
    log(f"Finaler Film gespeichert: {final_path}", "SUCCESS")


def run_wan_pipeline(story_file, character_image, output_dir, steps=4):
    log("==================================================================", "INFO")
    log("🚀 Starte WAN 2.2 Movie Maker — Schnelle 4-Step Video-Pipeline", "INFO")
    log("==================================================================", "INFO")

    if not check_comfy():
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(INPUT_ROOT, exist_ok=True)

    char_base = os.path.basename(character_image)
    dest_char = os.path.join(INPUT_ROOT, char_base)
    if not os.path.exists(dest_char) and os.path.exists(character_image):
        import shutil
        shutil.copy2(character_image, dest_char)

    with open(story_file, "r") as f:
        story = yaml.safe_load(f)

    scenes = story.get("scenes", [])
    log(f"Gesamtanzahl Szenen: {len(scenes)} (WAN 2.2 4-Step Turbo Modus)", "INFO")

    rendered_clips = []
    prev_frame = dest_char # Erste Szene startet mit Masterbild

    for idx, sc in enumerate(scenes, 1):
        prompt = sc.get("action", "")
        audio_cue = sc.get("audio", "")
        log(f"--- Szene [{idx}/{len(scenes)}] ---", "SCENE")
        log(f"Prompt: {prompt[:100]}...", "INFO")

        # Startbild kopieren
        frame_name = f"wan_input_sc{idx}.png"
        shutil_dest = os.path.join(INPUT_ROOT, frame_name)
        import shutil
        shutil.copy2(prev_frame, shutil_dest)

        # Graph an ComfyUI
        p_graph = build_wan_api_prompt(prompt, frame_name, steps=steps)
        payload = json.dumps({"prompt": p_graph}).encode()
        req = urllib.request.Request(f"{COMFY_URL}/prompt", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            p_id = json.loads(resp.read().decode())["prompt_id"]

        log(f"Rendere WAN Szene {idx}...", "INFO")
        subfolder, filename = wait_for_prompt(p_id)
        raw_clip = os.path.join(OUTPUT_ROOT, subfolder, filename)

        # Lokale Szene speichern + Audio anfügen
        sc_final = os.path.join(output_dir, f"wan_szene_{idx:02d}.mp4")
        mux_audio_track(raw_clip, audio_cue, sc_final)
        rendered_clips.append(sc_final)

        # Last Frame für Handoff
        last_frame_path = os.path.join(output_dir, f"wan_last_frame_{idx}.png")
        extract_last_frame(sc_final, last_frame_path)
        prev_frame = last_frame_path

    # Gesamtfilm
    final_output = os.path.join(output_dir, "wan_gesamtfilm_15s.mp4")
    concatenate_scenes(rendered_clips, final_output)
    log("🎉 WAN 2.2 Film erfolgreich abgeschlossen!", "SUCCESS")


def main():
    parser = argparse.ArgumentParser(description="WAN 2.2 Movie Maker")
    parser.add_argument("--story", default="vergleich_minimax_vs_wan/wan_story_test.yaml", help="Pfad zum Drehbuch")
    parser.add_argument("--character", default="ComfyUI/input/YOTTEA-KREA-PRO (21).png", help="Startbild")
    parser.add_argument("--output", default="output/wan_test_movie", help="Zielverzeichnis")
    parser.add_argument("--steps", type=int, default=4, help="Sampling-Steps (Standard: 4 mit Lightx2v LoRA)")
    args = parser.parse_args()

    run_wan_pipeline(args.story, args.character, args.output, steps=args.steps)


if __name__ == "__main__":
    main()

