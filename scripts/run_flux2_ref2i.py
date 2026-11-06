#!/usr/bin/env python3
"""
scripts/run_flux2_ref2i.py
Führt den Flux 2 Dual-Reference-to-Image (Ref2I / ReV2I) Workflow auf ComfyUI aus.
Verschmilzt zwei Quellbilder (<Picture 1> und <Picture 2>) in ein neues Zielbild.
"""

import os
import sys
import json
import time
import shutil
import random
import argparse
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
INPUT_DIR = os.path.join(PROJECT_ROOT, "ComfyUI", "input")
COMFY_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "ComfyUI", "output")
TARGET_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "flux2_ref2i")

COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_BLUE = "\033[94m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"


def log(msg, level="INFO"):
    timestamp = time.strftime("%H:%M:%S")
    if level == "INFO":
        print(f"{COLOR_BLUE}[INFO {timestamp}]{COLOR_RESET} {msg}")
    elif level == "SUCCESS":
        print(f"{COLOR_GREEN}[OK {timestamp}]{COLOR_RESET} {msg}")
    elif level == "WARN":
        print(f"{COLOR_YELLOW}[WARN {timestamp}]{COLOR_RESET} {msg}")
    elif level == "ERROR":
        print(f"{COLOR_RED}[ERROR {timestamp}]{COLOR_RESET} {msg}")
    else:
        print(f"[{level}] {msg}")


def check_comfyui_online(base_url):
    try:
        req = urllib.request.Request(f"{base_url}/system_stats")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def prepare_image(image_path, target_input_dir):
    """Kopiert oder verifiziert das Bild im ComfyUI/input Verzeichnis."""
    os.makedirs(target_input_dir, exist_ok=True)
    if os.path.exists(image_path):
        filename = os.path.basename(image_path)
        dest = os.path.join(target_input_dir, filename)
        if not os.path.exists(dest) or os.path.getsize(dest) != os.path.getsize(image_path):
            shutil.copy2(image_path, dest)
            log(f"Referenzbild kopiert: {image_path} -> {dest}")
        return filename
    else:
        # Prüfe ob Bild bereits in ComfyUI/input liegt
        in_comfy = os.path.join(target_input_dir, image_path)
        if os.path.exists(in_comfy):
            return image_path
        raise FileNotFoundError(f"Referenzbild nicht gefunden: {image_path}")


def build_ref2i_prompt(
    image1_name,
    image2_name,
    prompt_text,
    width=1024,
    height=1024,
    turbo=False,
    steps=None,
    guidance=3.5,
    seed=None,
    prefix="Flux2_Dual_Ref2I"
):
    """Erzeugt das ComfyUI API-Prompt-Dictionary für Flux 2 Dual Ref2I."""
    if seed is None:
        seed = random.randint(100000000, 999999999999999)
    if steps is None:
        steps = 8 if turbo else 20

    api_dict = {
        "1": {
            "inputs": {
                "unet_name": "flux2_dev_fp8mixed.safetensors",
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader"
        },
        "3": {
            "inputs": {
                "clip_name": "mistral_3_small_flux2_fp8.safetensors",
                "type": "flux2",
                "device": "default"
            },
            "class_type": "CLIPLoader"
        },
        "4": {
            "inputs": {
                "vae_name": "flux2-vae.safetensors"
            },
            "class_type": "VAELoader"
        },
        "5": {
            "inputs": {
                "image": image1_name
            },
            "class_type": "LoadImage"
        },
        "6": {
            "inputs": {
                "pixels": ["5", 0],
                "vae": ["4", 0]
            },
            "class_type": "VAEEncode"
        },
        "7": {
            "inputs": {
                "image": image2_name
            },
            "class_type": "LoadImage"
        },
        "8": {
            "inputs": {
                "pixels": ["7", 0],
                "vae": ["4", 0]
            },
            "class_type": "VAEEncode"
        },
        "9": {
            "inputs": {
                "text": prompt_text,
                "clip": ["3", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        "10": {
            "inputs": {
                "guidance": float(guidance),
                "conditioning": ["9", 0]
            },
            "class_type": "FluxGuidance"
        },
        "11": {
            "inputs": {
                "conditioning": ["10", 0],
                "latent": ["6", 0]
            },
            "class_type": "ReferenceLatent"
        },
        "12": {
            "inputs": {
                "conditioning": ["11", 0],
                "latent": ["8", 0]
            },
            "class_type": "ReferenceLatent"
        },
        "13": {
            "inputs": {
                "width": int(width),
                "height": int(height),
                "batch_size": 1
            },
            "class_type": "EmptyFlux2LatentImage"
        },
        "14": {
            "inputs": {
                "steps": int(steps),
                "width": int(width),
                "height": int(height)
            },
            "class_type": "Flux2Scheduler"
        },
        "15": {
            "inputs": {
                "model": ["2", 0] if turbo else ["1", 0],
                "conditioning": ["12", 0]
            },
            "class_type": "BasicGuider"
        },
        "16": {
            "inputs": {
                "sampler_name": "euler"
            },
            "class_type": "KSamplerSelect"
        },
        "17": {
            "inputs": {
                "noise_seed": int(seed)
            },
            "class_type": "RandomNoise"
        },
        "18": {
            "inputs": {
                "noise": ["17", 0],
                "guider": ["15", 0],
                "sampler": ["16", 0],
                "sigmas": ["14", 0],
                "latent_image": ["13", 0]
            },
            "class_type": "SamplerCustomAdvanced"
        },
        "19": {
            "inputs": {
                "samples": ["18", 0],
                "vae": ["4", 0]
            },
            "class_type": "VAEDecode"
        },
        "20": {
            "inputs": {
                "filename_prefix": prefix,
                "images": ["19", 0]
            },
            "class_type": "SaveImage"
        }
    }
    if turbo:
        api_dict["2"] = {
            "inputs": {
                "model": ["1", 0],
                "lora_name": "Flux_2-Turbo-LoRA_comfyui.safetensors",
                "strength_model": 1.0
            },
            "class_type": "LoraLoaderModelOnly"
        }
    return api_dict, seed


def queue_prompt(prompt_dict, base_url):
    payload = json.dumps({"prompt": prompt_dict}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/prompt", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        return res.get("prompt_id")


def wait_for_completion(prompt_id, base_url, timeout=600):
    start = time.time()
    last_dot = start
    while time.time() - start < timeout:
        elapsed = time.time() - start
        try:
            req = urllib.request.Request(f"{base_url}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                if prompt_id in data:
                    item = data[prompt_id]
                    status_info = item.get("status", {})
                    if status_info.get("status_str") == "error":
                        raise RuntimeError(f"ComfyUI Ausführungsfehler: {status_info.get('messages', [])}")
                    outputs = item.get("outputs", {})
                    for nid, out in outputs.items():
                        if "images" in out and out["images"]:
                            img_info = out["images"][0]
                            print()
                            log(f"Prompt {prompt_id} abgeschlossen in {elapsed:.1f}s!", "SUCCESS")
                            return img_info.get("subfolder", ""), img_info.get("filename")
        except urllib.error.URLError:
            pass
        
        if time.time() - last_dot >= 3.0:
            sys.stdout.write(".")
            sys.stdout.flush()
            last_dot = time.time()
        time.sleep(1.0)
    raise TimeoutError(f"Rendering hat das Timeout von {timeout}s überschritten.")


def main():
    parser = argparse.ArgumentParser(description="Flux 2 Dual Reference-to-Image (Ref2I / ReV2I Fusion)")
    parser.add_argument("--image1", type=str, default="detective_cross.png", help="Pfad zu Referenzbild 1 (<Picture 1>)")
    parser.add_argument("--image2", type=str, default="elena_vance.png", help="Pfad zu Referenzbild 2 (<Picture 2>)")
    parser.add_argument("--prompt", type=str, default=(
        "High-end cinematic aesthetic, 35mm Arri Alexa 65 cinematography: <Picture 1> detective and <Picture 2> "
        "athletic woman standing together in a luxury modern penthouse, warm golden volumetric lighting, "
        "shallow depth of field, anamorphic lens flares, photorealistic skin texture, 8k resolution"
    ), help="Regie-Prompt mit <Picture 1> und <Picture 2>")
    parser.add_argument("--width", type=int, default=1024, help="Breite (Standard: 1024)")
    parser.add_argument("--height", type=int, default=1024, help="Höhe (Standard: 1024)")
    parser.add_argument("--turbo", action="store_true", default=True, help="Nutze Turbo-LoRA (Standard: True)")
    parser.add_argument("--no-turbo", dest="turbo", action="store_false", help="Deaktiviere Turbo-LoRA (Nutze reine Dev-Qualität mit 20 Steps)")
    parser.add_argument("--steps", type=int, default=None, help="Sampling Steps (Standard: 8 bei Turbo, 20 bei Dev)")
    parser.add_argument("--guidance", type=float, default=3.5, help="Flux Guidance Scale (Standard: 3.5)")
    parser.add_argument("--seed", type=int, default=None, help="Noise Seed (Standard: Zufall)")
    parser.add_argument("--output-name", type=str, default=None, help="Zieldateiname (Standard: timestamp_prefix)")
    parser.add_argument("--comfy-url", type=str, default=DEFAULT_COMFY_URL, help="ComfyUI URL")

    args = parser.parse_args()

    print(f"\n{COLOR_CYAN}{COLOR_BOLD}=================================================================={COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD} 🎨 FLUX 2 DUAL REFERENCE-TO-IMAGE (Ref2I / ReV2I FUSION){COLOR_RESET}")
    print(f"{COLOR_CYAN}{COLOR_BOLD}=================================================================={COLOR_RESET}\n")

    if not check_comfyui_online(args.comfy_url):
        log(f"ComfyUI ist unter {args.comfy_url} nicht erreichbar!", "ERROR")
        log("Starte ComfyUI mit: ./start_comfyui.sh", "INFO")
        sys.exit(1)

    # 1. Referenzbilder vorbereiten
    img1_file = prepare_image(args.image1, INPUT_DIR)
    img2_file = prepare_image(args.image2, INPUT_DIR)
    log(f"Referenz 1 (<Picture 1>): {img1_file}", "INFO")
    log(f"Referenz 2 (<Picture 2>): {img2_file}", "INFO")

    # 2. Prompt bauen
    effective_steps = args.steps if args.steps else (8 if args.turbo else 20)
    mode_label = f"Turbo-LoRA ({effective_steps} Steps)" if args.turbo else f"Dev Quality ({effective_steps} Steps)"
    log(f"Modus: {mode_label} | Auflösung: {args.width}x{args.height} | Guidance: {args.guidance}", "INFO")
    log(f"Prompt: {args.prompt[:120]}...", "INFO")

    prompt_dict, seed = build_ref2i_prompt(
        image1_name=img1_file,
        image2_name=img2_file,
        prompt_text=args.prompt,
        width=args.width,
        height=args.height,
        turbo=args.turbo,
        steps=effective_steps,
        guidance=args.guidance,
        seed=args.seed
    )

    log(f"Verwende Seed: {seed}", "INFO")

    # 3. An ComfyUI übergeben
    log("Übergebe Prompt an ComfyUI API...", "INFO")
    prompt_id = queue_prompt(prompt_dict, args.comfy_url)
    log(f"Prompt in Queue (ID: {prompt_id}). Rendere Bild...", "INFO")

    # 4. Warten auf Fertigstellung
    subfolder, filename = wait_for_completion(prompt_id, args.comfy_url)

    # 5. Bild einsammeln & in Zielverzeichnis ablegen
    src_path = os.path.join(COMFY_OUTPUT_DIR, subfolder, filename)
    os.makedirs(TARGET_OUTPUT_DIR, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    target_filename = args.output_name if args.output_name else f"flux2_fusion_{timestamp}.png"
    if not target_filename.lower().endswith(".png"):
        target_filename += ".png"
    target_path = os.path.join(TARGET_OUTPUT_DIR, target_filename)

    if os.path.exists(src_path):
        shutil.copy2(src_path, target_path)
        log(f"Neues Fusions-Bild gespeichert unter: {COLOR_BOLD}{target_path}{COLOR_RESET}", "SUCCESS")
    else:
        log(f"Quelldatei in ComfyUI nicht gefunden: {src_path}", "WARN")

    print(f"\n{COLOR_GREEN}{COLOR_BOLD}✅ Dual Ref2I Fusion erfolgreich abgeschlossen!{COLOR_RESET}\n")


if __name__ == "__main__":
    main()

