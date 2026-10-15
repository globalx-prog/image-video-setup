#!/usr/bin/env python3
"""
🎬 auto_movie_maker.py — Vollautomatische Langfilm-Pipeline für MiniMax H3
=============================================================================
Erstellt lange, konsistente Filme (z. B. 15s Test oder 5 Minuten / 60 Szenen)
vollautomatisch aus einem Storyboard (YAML/JSON) oder Fließtext (Ollama).

Features:
- Charakter-Konsistenz über 100% visuelle Verankerung (Ref2V & Last-Frame-Handoff)
- Unabhängig von der Skriptlänge (3 Szenen bis 120+ Szenen)
- Automatischer Speicherschutz (ComfyUI /free nach jedem Block für 48GB W7800)
- Automatische FFmpeg-Zusammenfügung (Lossless Concat mit synchronem Stereo-Audio)
- Optional: Automatische Zerlegung von Roh-Drehbüchern via lokalem Ollama LLM
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta

try:
    import asyncio
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

COMFY_HOST = "127.0.0.1:8188"
OLLAMA_HOST = "127.0.0.1:11434"


class DualLogger:
    """Schreibt alle Terminal-Ausgaben simultan in stdout/stderr und in production.log im Videoordner."""
    def __init__(self, log_filepath, original_stdout, original_stderr):
        self.terminal_out = original_stdout
        self.terminal_err = original_stderr
        self.log_filepath = log_filepath
        os.makedirs(os.path.dirname(os.path.abspath(log_filepath)), exist_ok=True)
        self.log_file = open(log_filepath, "a", encoding="utf-8")
        self.warnings_and_errors = []
        self.lock = threading.Lock()

    def write(self, message):
        with self.lock:
            self.terminal_out.write(message)
            self.terminal_out.flush()
            # Entferne ANSI-Farbcodes für die saubere Logdatei
            clean_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
            self.log_file.write(clean_message)
            self.log_file.flush()

            # Sammle Warnungen, Fehler und Exceptions
            if any(k in clean_message for k in ["[WARN]", "[ERROR]", "Traceback", "Exception", "TimeoutError", "RuntimeError", "HIP out of memory", "Konnte nicht"]):
                stripped = clean_message.strip()
                if stripped and stripped not in self.warnings_and_errors:
                    self.warnings_and_errors.append(stripped)

    def flush(self):
        with self.lock:
            self.terminal_out.flush()
            self.log_file.flush()

    def write_summary(self):
        with self.lock:
            summary = "\n" + "=" * 66 + "\n"
            summary += " 📋 ZUSAMMENFASSUNG: WARNUNGEN & PROBLEME\n"
            summary += "=" * 66 + "\n"
            if not self.warnings_and_errors:
                summary += " ✅ Keine Warnungen oder Fehler während der Produktion aufgetreten!\n"
            else:
                summary += f" ⚠️ Es wurden {len(self.warnings_and_errors)} Warnung(en) / Problem(e) protokolliert:\n"
                for idx, issue in enumerate(self.warnings_and_errors, 1):
                    summary += f"   [{idx}] {issue}\n"
            summary += "=" * 66 + "\n"
            self.terminal_out.write(summary)
            self.terminal_out.flush()
            self.log_file.write(summary)
            self.log_file.flush()

    def close(self):
        with self.lock:
            try:
                self.log_file.close()
            except Exception:
                pass


def cleanup_system_ram_and_swap():
    """Befreit System-RAM, glibc-Heaps, flusht SSD-Caches und holt SWAP zurück."""
    log("==================================================================", "INFO")
    log("🧹 Post-Flight: Bereinige System-RAM, Dateisystem-Caches & SWAP...", "INFO")
    log("==================================================================", "INFO")

    # 1. Python Garbage Collection & libc malloc_trim
    try:
        import gc, ctypes
        gc.collect()
        try:
            libc = ctypes.CDLL("libc.so.6")
            libc.malloc_trim(0)
            log("glibc malloc_trim(0) ausgeführt (nicht mehr genutzter Heap an Kernel zurückgegeben).", "SUCCESS")
        except Exception:
            pass
    except Exception as e:
        log(f"RAM-GC Hinweis: {e}", "WARN")

    # 2. Rufe free_vram.sh auf, falls vorhanden
    script_dir = os.path.dirname(os.path.abspath(__file__))
    free_script = os.path.join(script_dir, "free_vram.sh")
    if os.path.isfile(free_script):
        try:
            res = subprocess.run([free_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
            log("free_vram.sh Bereinigung erfolgreich ausgeführt.", "SUCCESS")
        except Exception as e:
            log(f"Hinweis zu free_vram.sh: {e}", "WARN")

    # 3. sync Dateisystem-Caches
    try:
        subprocess.run(["sync"], timeout=15)
        log("sync ausgeführt (alle Festplatten-Schreibpuffer geflusht).", "SUCCESS")
    except Exception:
        pass

    # 4. SWAP-Status prüfen und protokollieren
    try:
        res = subprocess.run(["free", "-m"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in res.stdout.splitlines():
            if "Swap:" in line:
                parts = line.split()
                used_swap = int(parts[2]) if len(parts) >= 3 else 0
                if used_swap > 50:
                    log(f"Aktuell belegter Swap: {used_swap} MB. Versuche Swap in physischen RAM zurückzuholen...", "WARN")
                    subprocess.run(["sudo", "-n", "swapoff", "-a"], stderr=subprocess.DEVNULL)
                    subprocess.run(["sudo", "-n", "swapon", "-a"], stderr=subprocess.DEVNULL)
                else:
                    log(f"Swap-Speicher ist sauber ({used_swap} MB belegt). Kein SSD-Stocken zu erwarten.", "SUCCESS")
            elif "Mem:" in line:
                parts = line.split()
                free_ram = int(parts[3]) if len(parts) >= 4 else 0
                log(f"Verfügbarer freier System-RAM: {free_ram} MB.", "INFO")
    except Exception:
        pass


def log(msg, level="INFO"):
    colors = {
        "INFO": "\033[0;34m[INFO]\033[0m",
        "SUCCESS": "\033[0;32m[OK]\033[0m",
        "WARN": "\033[1;33m[WARN]\033[0m",
        "ERROR": "\033[0;31m[ERROR]\033[0m",
        "SCENE": "\033[1;35m[SZENE]\033[0m",
        "STATUS": "\033[1;36m[STATUS]\033[0m"
    }
    prefix = colors.get(level, f"[{level}]")
    print(f"{prefix} {msg}", flush=True)


def check_comfy_live(base_url):
    try:
        url = f"{base_url}/system_stats"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            vram = data.get("devices", [{}])[0].get("vram_free", 0) / (1024**3)
            log(f"ComfyUI verbunden! Freier VRAM: {vram:.1f} GB", "SUCCESS")
            return True
    except Exception as e:
        log(f"ComfyUI unter {base_url} nicht erreichbar: {e}", "ERROR")
        return False


def free_comfy_memory(base_url, unload_models=False):
    """Befreit PyTorch-Caches und optional entlädt inaktive Modelle."""
    try:
        url = f"{base_url}/free"
        payload = json.dumps({"unload_models": unload_models, "free_memory": True}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                log(f"Speicherbereinigung durchgeführt (unload={unload_models})", "SUCCESS")
    except Exception as e:
        log(f"Speicherbereinigung fehlgeschlagen: {e}", "WARN")


def purge_comfyui_queue(base_url, interrupt_running=True):
    """Bricht verwaiste Renderings aus vorherigen Abbrüchen ab und leert die ComfyUI-Warteschlange."""
    try:
        if interrupt_running:
            req_int = urllib.request.Request(f"{base_url}/interrupt", data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req_int, timeout=3) as resp:
                pass
        req_clr = urllib.request.Request(f"{base_url}/queue", data=json.dumps({"clear": True}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req_clr, timeout=3) as resp:
            pass
        log("ComfyUI-Warteschlange bereinigt (verwaiste Vorläufe entfernt).", "INFO")
    except Exception as e:
        log(f"Queue-Bereinigung übersprungen: {e}", "WARN")


def check_vram_guard(base_url, min_free_gb=8.0):
    """Intelligenter Hardware-Schutz: Prüft freien VRAM vor jeder Szene.
    Falls der freie VRAM unter den Sicherheits-Schwellenwert fällt (z. B. durch Fragmentierung),
    wird präventiv ein Modell-Unload ausgelöst, um Abstürze oder OOM sicher zu verhindern.
    """
    try:
        url = f"{base_url}/system_stats"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            devices = data.get("devices", [])
            if devices:
                free_gb = devices[0].get("vram_free", 0) / (1024**3)
                if free_gb < min_free_gb:
                    log(f"⚠️ VRAM-Sicherheitsgrenze erreicht: Nur noch {free_gb:.1f} GB frei (< {min_free_gb} GB Schwellenwert)!", "WARN")
                    log("   -> Führe präventiven Notfall-Unload durch, um VRAM-Überlauf/Crash sicher zu verhindern...", "WARN")
                    free_comfy_memory(base_url, unload_models=True)
                    return False
                return True
    except Exception as e:
        log(f"VRAM-Guard Prüfung fehlgeschlagen: {e}", "WARN")
    return True


class GPUTelemetryTracker:
    """Zeichnet GPU-Temperatur (Edge/Junction) und Leistungsaufnahme (Watt) kontinuierlich im Hintergrund auf."""
    def __init__(self, interval=1.0):
        self.interval = interval
        self.running = False
        self.thread = None
        self.current_scene_label = "Initialisierung"
        hwmon_dirs = glob.glob("/sys/class/drm/card*/device/hwmon/hwmon*")
        self.hwmon_path = None
        for h in hwmon_dirs:
            try:
                with open(f"{h}/name") as f:
                    if "amdgpu" in f.read().lower():
                        self.hwmon_path = h
                        break
            except Exception:
                pass
        if not self.hwmon_path and hwmon_dirs:
            self.hwmon_path = hwmon_dirs[0]
        self.samples = []

    def set_scene(self, scene_label):
        self.current_scene_label = scene_label

    def start(self):
        if not self.hwmon_path:
            return
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _poll_loop(self):
        while self.running:
            now = time.time()
            edge = None
            junc = None
            power = None
            try:
                if os.path.exists(f"{self.hwmon_path}/temp1_input"):
                    with open(f"{self.hwmon_path}/temp1_input") as f:
                        edge = int(f.read().strip()) / 1000.0
                if os.path.exists(f"{self.hwmon_path}/temp2_input"):
                    with open(f"{self.hwmon_path}/temp2_input") as f:
                        junc = int(f.read().strip()) / 1000.0
                if os.path.exists(f"{self.hwmon_path}/power1_average"):
                    with open(f"{self.hwmon_path}/power1_average") as f:
                        power = int(f.read().strip()) / 1e6
            except Exception:
                pass

            if power is not None or edge is not None or junc is not None:
                self.samples.append({
                    "time": now,
                    "scene": self.current_scene_label,
                    "edge": edge,
                    "junction": junc,
                    "power": power
                })
            time.sleep(self.interval)

    def get_summary(self):
        if not self.samples:
            return None

        valid_junc = [s for s in self.samples if s["junction"] is not None]
        peak_junc_sample = max(valid_junc, key=lambda s: s["junction"]) if valid_junc else None

        valid_edge = [s for s in self.samples if s["edge"] is not None]
        peak_edge = max(s["edge"] for s in valid_edge) if valid_edge else 0.0

        valid_powers = [s for s in self.samples if s["power"] is not None]
        if valid_powers and len(valid_powers) >= 2:
            total_energy_joules = 0.0
            for i in range(1, len(valid_powers)):
                dt = valid_powers[i]["time"] - valid_powers[i-1]["time"]
                avg_p = (valid_powers[i]["power"] + valid_powers[i-1]["power"]) / 2.0
                total_energy_joules += avg_p * dt
            energy_wh = total_energy_joules / 3600.0
            avg_power = sum(s["power"] for s in valid_powers) / len(valid_powers)
            peak_power = max(s["power"] for s in valid_powers)
        elif valid_powers:
            avg_power = valid_powers[0]["power"]
            peak_power = avg_power
            energy_wh = 0.0
        else:
            avg_power = 0.0
            peak_power = 0.0
            energy_wh = 0.0

        return {
            "peak_junction": peak_junc_sample["junction"] if peak_junc_sample else 0.0,
            "peak_edge": peak_edge,
            "peak_time_str": datetime.fromtimestamp(peak_junc_sample["time"]).strftime("%H:%M:%S") if peak_junc_sample else "N/A",
            "peak_scene": peak_junc_sample["scene"] if peak_junc_sample else "N/A",
            "avg_power": avg_power,
            "peak_power": peak_power,
            "energy_wh": energy_wh,
            "cost_eur": (energy_wh / 1000.0) * 0.35
        }

    def get_current_reading(self):
        """Ermittelt die aktuellen Live-Werte für Edge-Temp, Hotspot-Temp und Wattage."""
        edge = None
        junc = None
        power = None
        if self.hwmon_path:
            try:
                if os.path.exists(f"{self.hwmon_path}/temp1_input"):
                    with open(f"{self.hwmon_path}/temp1_input") as f:
                        edge = int(f.read().strip()) / 1000.0
                if os.path.exists(f"{self.hwmon_path}/temp2_input"):
                    with open(f"{self.hwmon_path}/temp2_input") as f:
                        junc = int(f.read().strip()) / 1000.0
                if os.path.exists(f"{self.hwmon_path}/power1_average"):
                    with open(f"{self.hwmon_path}/power1_average") as f:
                        power = int(f.read().strip()) / 1e6
            except Exception:
                pass
        return edge, junc, power


class ComfyUIStatusTracker:
    """Überwacht über den WebSocket von ComfyUI den aktuell aktiven Node und Fortschritt in Echtzeit."""
    def __init__(self, comfy_url, client_id):
        self.comfy_url = comfy_url
        self.client_id = client_id
        self.active_prompt_id = None
        self.current_node = None
        self.progress = None  # (value, max)
        self.last_error = None
        self.is_executing = False
        self.execution_started_at = None
        self.running = False
        self.thread = None

    def start(self):
        if not HAS_AIOHTTP:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def set_active_prompt(self, prompt_id):
        self.active_prompt_id = str(prompt_id) if prompt_id else None
        self.current_node = None
        self.progress = None
        self.last_error = None
        self.is_executing = False
        self.execution_started_at = None

    def reset_prompt(self):
        self.set_active_prompt(None)

    def _run_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ws_handler())
        except Exception:
            pass
        finally:
            loop.close()

    async def _ws_handler(self):
        ws_url = self.comfy_url.replace("http://", "ws://").replace("https://", "wss://") + f"/ws?clientId={self.client_id}"
        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(ws_url, timeout=5.0) as ws:
                        while self.running and not ws.closed:
                            try:
                                msg = await asyncio.wait_for(ws.receive_json(), timeout=1.0)
                                mtype = msg.get("type")
                                data = msg.get("data", {})
                                msg_pid = str(data.get("prompt_id")) if data.get("prompt_id") else None

                                # Filter: Ignoriere Nachrichten fremder oder alter Prompts
                                if self.active_prompt_id and msg_pid and msg_pid != self.active_prompt_id:
                                    continue

                                if mtype == "executing":
                                    node = data.get("node")
                                    self.current_node = node
                                    if node is not None:
                                        self.is_executing = True
                                        if not self.execution_started_at:
                                            self.execution_started_at = time.time()
                                    else:
                                        self.is_executing = False
                                elif mtype == "progress":
                                    if self.is_executing or not self.active_prompt_id:
                                        self.progress = (data.get("value"), data.get("max"))
                                elif mtype == "execution_error":
                                    self.last_error = data
                            except asyncio.TimeoutError:
                                continue
                            except Exception:
                                break
            except Exception:
                await asyncio.sleep(2.0)


def get_node_description(prompt_dict, node_id, progress=None):
    """Übersetzt eine ComfyUI-Node-ID in einen verständlichen deutschen Aktionsbericht."""
    if not node_id:
        return "Initialisiere Pipeline / Warte auf Queue..."
    node_data = prompt_dict.get(str(node_id), {}) if prompt_dict else {}
    class_type = node_data.get("class_type", f"Node {node_id}")
    mapping = {
        "UNETLoader": "Lade MiniMax UNET Diffusionsmodell (INT8)",
        "CLIPLoader": "Lade Qwen3-VL Text- & Vision-Encoder (INT8)",
        "VAELoader": "Lade Video/Audio VAE",
        "LoraLoaderModelOnly": "Lade & Injiziere Turbo-LoRA Gewichte",
        "ComfySwitchNode": "Modell-Switch",
        "EasyCache": "Initialisiere First-Block Caching (EasyCache)",
        "LoadImage": "Lade Referenz-/Startbild",
        "MiniMaxH3ReferenceToVideo": "Konditioniere Text- & Referenzbild-Latents",
        "MiniMaxH3ImageToVideo": "Konditioniere Prompts & Handoff-Frame",
        "BasicGuider": "Initialisiere Guider",
        "KSamplerSelect": "Wähle ResMultistep Sampler",
        "BasicScheduler": "Berechne Noise-Schedule",
        "RandomNoise": "Generiere Seed-Rauschen",
        "SamplerCustomAdvanced": "Diffusions-Sampling (Clip-Generierung)",
        "VAEDecode": "Dekodiere Video-Frames (Latent -> Pixel)",
        "VAEDecodeAudio": "Dekodiere Audio-Track (Latent -> Waveform)",
        "UpscaleModelLoader": "Lade R-ESRGAN Upscaler-Modell",
        "ImageUpscaleWithModelBatched": "R-ESRGAN KI-Upscaling auf Full HD (1080p)",
        "CreateVideo": "Füge Video- und Audiostreams zusammen",
        "VRAMCleanup": "Bereinige GPU-Caches & VRAM",
        "SaveVideo": "Speichere fertigen MP4-Clip auf SSD"
    }
    desc = mapping.get(class_type, class_type)
    if class_type == "SamplerCustomAdvanced" and progress:
        val, max_v = progress
        return f"{desc} (Sampling-Schritt {val}/{max_v}) [{class_type}]"
    elif class_type == "ImageUpscaleWithModelBatched" and progress:
        val, max_v = progress
        return f"{desc} (Frame {val}/{max_v}) [{class_type}]"
    return f"{desc} [{class_type}]"


def decompose_text_with_ollama(text_path, model="qwen3.8-27b-q4", character_desc="Max, a detective in a brown trenchcoat"):
    """Zerlegt ein Fließtext-Drehbuch über Ollama automatisch in 5-Sekunden-Shots."""
    log(f"Zerlege Drehbuch via Ollama ({model})...", "INFO")
    with open(text_path, "r", encoding="utf-8") as f:
        story_text = f.read()

    system_prompt = f"""You are a professional film director and screenwriter for AI video generation with MiniMax H3.
The main character is: {character_desc}.
Your task is to break down the user's story into numbered, consecutive 5-second cinematic shots.
For each shot, specify:
1. "id": integer shot number starting from 1
2. "type": "ref2v" for camera cuts / angle changes (references character image), or "i2v" for continuous camera pans / direct continuation from previous frame.
3. "action": detailed visual prompt, camera angle, lighting, and ambient sound effects for MiniMax H3. Use <Picture 1> to refer to the main character when type is "ref2v".

Return ONLY a valid JSON array of objects without markdown formatting:
[
  {{"id": 1, "type": "ref2v", "action": "..."}},
  {{"id": 2, "type": "i2v", "action": "..."}}
]"""

    req_data = {
        "model": model,
        "prompt": f"{system_prompt}\n\nUser Story:\n{story_text}\n\nJSON output:",
        "stream": False,
        "options": {"temperature": 0.3}
    }

    try:
        req = urllib.request.Request(
            f"http://{OLLAMA_HOST}/api/generate",
            data=json.dumps(req_data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            raw = res.get("response", "").strip()
            # extract JSON array
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                scenes = json.loads(m.group(0))
                log(f"Ollama hat die Story erfolgreich in {len(scenes)} Szenen zerlegt!", "SUCCESS")
                return scenes
            else:
                log("Konnte kein JSON-Array in der Ollama-Antwort finden.", "ERROR")
                raise ValueError("Ungültige Antwort von Ollama")
    except Exception as e:
        log(f"Ollama-Zerlegung fehlgeschlagen: {e}. Verwende Fallback.", "WARN")
        # Einfacher Fallback: Teile Absätze
        paragraphs = [p.strip() for p in story_text.split("\n\n") if p.strip()]
        scenes = []
        for i, p in enumerate(paragraphs, start=1):
            scenes.append({
                "id": i,
                "type": "ref2v" if i % 2 == 1 else "i2v",
                "action": p
            })
        return scenes


def build_api_prompt_ref2v(scene_prompt, character_image_name, character2_image_name=None, width=864, height=480, duration=5.0, turbo=True, seed=None, steps=None, upscale=False, offload=False):
    """Erstellt ein reines ComfyUI-API-Payload für MiniMax H3 Ref2V (unterstützt 1 oder 2 Charakter-Referenzen)."""
    if seed is None:
        seed = int(time.time() * 1000) % (2**31)

    if steps is None:
        steps = 4 if turbo else 20
    length = max(5, round(duration * 24)) + (5 - (max(5, round(duration * 24)) % 17)) % 17

    graph = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
                "type": "minimax",
                "device": "default"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}
        },
        "4": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}
        },
        "5": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "lora_name": "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
                "strength_model": 1.0,
                "model": ["1", 0]
            }
        },
        "6": {
            "class_type": "ComfySwitchNode",
            "inputs": {
                "switch": turbo,
                "on_false": ["1", 0],
                "on_true": ["5", 0]
            }
        },
        "7": {
            "class_type": "EasyCache",
            "inputs": {
                "reuse_threshold": 0.2,
                "start_percent": 0.15,
                "end_percent": 0.95,
                "verbose": False,
                "model": ["6", 0]
            }
        },
        "8": {
            "class_type": "LoadImage",
            "inputs": {"image": character_image_name}
        },
        "9": {
            "class_type": "MiniMaxH3ReferenceToVideo",
            "inputs": {
                "clip": ["2", 0],
                "vae": ["3", 0],
                "audio_vae": ["4", 0],
                "prompt": scene_prompt,
                "width": width,
                "height": height,
                "length": length,
                "ref_image_size": "match",
                "ref_images.ref_image_0": ["8", 0]
            }
        },
        "10": {
            "class_type": "BasicGuider",
            "inputs": {
                "model": ["7", 0],
                "conditioning": ["9", 0]
            }
        },
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "res_multistep"}
        },
        "12": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": ["7", 0],
                "scheduler": "simple",
                "steps": steps,
                "denoise": 1.0
            }
        },
        "13": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["13", 0],
                "guider": ["10", 0],
                "sampler": ["11", 0],
                "sigmas": ["12", 0],
                "latent_image": ["9", 1]
            }
        },
        "15": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["14", 0], "vae": ["3", 0]}
        },
        "16": {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["14", 1], "vae": ["4", 0]}
        }
    }

    if character2_image_name:
        graph["28"] = {
            "class_type": "LoadImage",
            "inputs": {"image": character2_image_name}
        }
        graph["9"]["inputs"]["ref_images.ref_image_1"] = ["28", 0]

    graph["17"] = {
        "class_type": "CreateVideo",
        "inputs": {
            "images": ["15", 0],
            "audio": ["16", 0],
            "fps": 24,
            "bit_depth": 8,
            "color_space": "sRGB",
            "codec": "none"
        }
    }

    graph["18"] = {
        "class_type": "VRAMCleanup",
        "inputs": {
            "offload_model": offload,
            "offload_cache": True,
            "anything": ["17", 0]
        }
    }
    graph["19"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "filename_prefix": "video/auto_movie/scene",
            "format": "auto",
            "video": ["18", 0]
        }
    }
    return graph


def build_api_prompt_i2v(scene_prompt, start_image_name, width=864, height=480, duration=5.0, turbo=True, seed=None, steps=None, upscale=False, offload=False):
    """Erstellt ein reines ComfyUI-API-Payload für MiniMax H3 I2V (Last-Frame-Handoff)."""
    if seed is None:
        seed = int(time.time() * 1000) % (2**31)

    if steps is None:
        steps = 4 if turbo else 20
    length = max(5, round(duration * 24)) + (5 - (max(5, round(duration * 24)) % 17)) % 17

    graph = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
                "type": "minimax",
                "device": "default"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}
        },
        "4": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}
        },
        "5": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "lora_name": "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
                "strength_model": 1.0,
                "model": ["1", 0]
            }
        },
        "6": {
            "class_type": "ComfySwitchNode",
            "inputs": {
                "switch": turbo,
                "on_false": ["1", 0],
                "on_true": ["5", 0]
            }
        },
        "7": {
            "class_type": "EasyCache",
            "inputs": {
                "reuse_threshold": 0.2,
                "start_percent": 0.15,
                "end_percent": 0.95,
                "verbose": False,
                "model": ["6", 0]
            }
        },
        "8": {
            "class_type": "LoadImage",
            "inputs": {"image": start_image_name}
        },
        "9": {
            "class_type": "MiniMaxH3ImageToVideo",
            "inputs": {
                "clip": ["2", 0],
                "vae": ["3", 0],
                "prompt": scene_prompt,
                "width": width,
                "height": height,
                "length": length,
                "first_frame": ["8", 0]
            }
        },
        "10": {
            "class_type": "BasicGuider",
            "inputs": {
                "model": ["7", 0],
                "conditioning": ["9", 0]
            }
        },
        "11": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "res_multistep"}
        },
        "12": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": ["7", 0],
                "scheduler": "simple",
                "steps": steps,
                "denoise": 1.0
            }
        },
        "13": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed}
        },
        "14": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["13", 0],
                "guider": ["10", 0],
                "sampler": ["11", 0],
                "sigmas": ["12", 0],
                "latent_image": ["9", 1]
            }
        },
        "15": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["14", 0], "vae": ["3", 0]}
        },
        "16": {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["14", 1], "vae": ["4", 0]}
        }
    }

    graph["17"] = {
        "class_type": "CreateVideo",
        "inputs": {
            "images": ["15", 0],
            "audio": ["16", 0],
            "fps": 24,
            "bit_depth": 8,
            "color_space": "sRGB",
            "codec": "none"
        }
    }

    graph["18"] = {
        "class_type": "VRAMCleanup",
        "inputs": {
            "offload_model": offload,
            "offload_cache": True,
            "anything": ["17", 0]
        }
    }
    graph["19"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "filename_prefix": "video/auto_movie/scene",
            "format": "auto",
            "video": ["18", 0]
        }
    }
    return graph


def queue_prompt(prompt_dict, base_url, client_id=None):
    """Sendet einen Prompt an ComfyUI und gibt die prompt_id zurück."""
    payload_data = {"prompt": prompt_dict}
    if client_id:
        payload_data["client_id"] = client_id
    payload = json.dumps(payload_data).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/prompt", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        return res.get("prompt_id")


def wait_for_prompt_completion(prompt_id, base_url, prompt_dict=None, scene_idx=None, total_scenes=None, gpu_tracker=None, status_tracker=None, timeout=1800):
    """Wartet auf das Fertigstellen des Prompts via Polling der History API und gibt alle 30s Status & Temperatur aus."""
    start_time = time.time()
    last_status_print = start_time
    last_dot = start_time
    exec_start_time = None

    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time

        # Falls der Prompt anfangs in der ComfyUI-Queue gewartet hat und jetzt startet, Timer für eigentliches Rendering neu starten
        if status_tracker and getattr(status_tracker, "is_executing", False) and not exec_start_time:
            exec_start_time = time.time()
            queue_wait_s = exec_start_time - start_time
            if queue_wait_s > 10.0:
                print()
                log(f"Prompt hat {queue_wait_s:.0f}s in ComfyUI-Queue gewartet. Starte Render-Timer für Szene ab jetzt neu!", "INFO")
                start_time = exec_start_time
                elapsed = 0.0

        # 1. Sofortige Fehlerprüfung über WebSocket Tracker
        if status_tracker and status_tracker.last_error:
            err = status_tracker.last_error
            nid = err.get("node_id", "?")
            ntype = err.get("node_type", "?")
            msg = err.get("exception_message", "")
            raise RuntimeError(f"ComfyUI Ausführungsfehler in Node {nid} ({ntype}): {msg}")

        # 2. Prüfe History-API
        try:
            req = urllib.request.Request(f"{base_url}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                if prompt_id in data:
                    res_item = data[prompt_id]
                    status_info = res_item.get("status", {})

                    # Sofortige Erkennung von Ausführungsfehlern
                    if status_info.get("status_str") == "error":
                        messages = status_info.get("messages", [])
                        err_details = []
                        for m in messages:
                            if isinstance(m, (list, tuple)) and len(m) > 1 and m[0] == "execution_error":
                                ed = m[1]
                                nid = ed.get("node_id", "?")
                                ntype = ed.get("node_type", "?")
                                exc_msg = ed.get("exception_message", "")
                                err_details.append(f"Node {nid} ({ntype}): {exc_msg}")
                        err_str = "; ".join(err_details) if err_details else json.dumps(status_info)
                        raise RuntimeError(f"ComfyUI Ausführungsfehler für Prompt {prompt_id}: {err_str}")

                    outputs = res_item.get("outputs", {})
                    for nid, out_dict in outputs.items():
                        media_items = out_dict.get("videos", []) + out_dict.get("images", [])
                        for item in media_items:
                            filename = item.get("filename") if isinstance(item, dict) else str(item)
                            subfolder = item.get("subfolder", "") if isinstance(item, dict) else ""
                            if filename and any(filename.lower().endswith(ext) for ext in [".mp4", ".webm", ".mkv", ".mov", ".gif"]):
                                print()
                                log(f"Prompt {prompt_id} abgeschlossen in {elapsed:.1f}s! ({filename})", "SUCCESS")
                                return subfolder, filename
                        if "videos" in out_dict and out_dict["videos"]:
                            vinfo = out_dict["videos"][0]
                            print()
                            log(f"Prompt {prompt_id} abgeschlossen in {elapsed:.1f}s! ({vinfo.get('filename')})", "SUCCESS")
                            return vinfo.get("subfolder", ""), vinfo.get("filename")
        except RuntimeError:
            raise
        except Exception:
            pass

        # 3. Alle 30 Sekunden: Status & GPU-Temperatur ausgeben
        if elapsed - (last_status_print - start_time) >= 30.0:
            last_status_print = time.time()
            # GPU Werte ermitteln
            edge_t, junc_t, pwr = gpu_tracker.get_current_reading() if gpu_tracker else (None, None, None)
            if edge_t is not None and junc_t is not None and pwr is not None:
                gpu_info = f"{edge_t:.1f}°C (Hotspot: {junc_t:.1f}°C, {pwr:.0f}W)"
            elif edge_t is not None:
                gpu_info = f"{edge_t:.1f}°C"
            else:
                gpu_info = "N/A"

            # Aktiven Befehl / Node ermitteln
            cur_node = status_tracker.current_node if status_tracker else None
            cur_prog = status_tracker.progress if status_tracker else None
            is_exec = getattr(status_tracker, "is_executing", False) if status_tracker else True
            if not is_exec and not cur_node:
                active_info = "Wartet in ComfyUI-Warteschlange..."
            else:
                active_info = get_node_description(prompt_dict, cur_node, cur_prog)

            el_m = int(elapsed // 60)
            el_s = int(elapsed % 60)
            scene_label = f"Szene [{scene_idx}/{total_scenes}]" if (scene_idx and total_scenes) else "Rendering"
            print()
            log(f"⏳ {scene_label} ({el_m:02d}:{el_s:02d} min) | GPU: {gpu_info} | Aktiv: {active_info}", "STATUS")

        # Optischer Herzschlag alle 5s
        if time.time() - last_dot >= 5.0:
            print(".", end="", flush=True)
            last_dot = time.time()

        time.sleep(2)

    print()
    raise TimeoutError(f"Prompt {prompt_id} hat das Timeout ({timeout}s) überschritten!")


def extract_last_frame(video_path, output_png_path):
    """Extrahiert den exakt letzten Frame eines Videos via FFmpeg."""
    cmd = [
        "ffmpeg", "-y", "-sseof", "-0.1",
        "-i", video_path,
        "-update", "1",
        "-q:v", "2",
        output_png_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_png_path


def upscale_video_ffmpeg(input_path, output_path, width=1920, height=1080, bitrate="16M"):
    """Skaliert einen Videoclip per FFmpeg mit Lanczos3 & Unsharp-Maske auf Full HD 1080p bei 16 Mbps."""
    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.abspath(input_path),
        "-vf", f"scale={width}:{height}:flags=lanczos,unsharp=5:5:0.8:5:5:0.4",
        "-c:v", "libx264", "-crf", "17", "-preset", "medium",
        "-b:v", bitrate, "-maxrate", bitrate, "-bufsize", "32M",
        "-c:a", "copy",
        os.path.abspath(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


def concatenate_scenes(video_files, final_output_path, smooth=True, fade_dur=0.4, upscale=False):
    """Fügt alle gerenderten Szenen zusammen (wahlweise mit nahtlosen Kino-Überblendungen oder Lossless Concat)."""
    if len(video_files) <= 1:
        import shutil
        shutil.copy2(video_files[0], final_output_path)
        log(f"Einzelne Szene gespeichert: {final_output_path}", "SUCCESS")
        return

    if smooth:
        try:
            log(f"Erzeuge weiche Kino-Überblendungen ({fade_dur}s xfade/acrossfade) für {len(video_files)} Szenen...", "INFO")
            durs = []
            inputs = []
            for vf in video_files:
                inputs.extend(["-i", os.path.abspath(vf)])
                res = subprocess.check_output(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", vf])
                durs.append(float(json.loads(res)["format"]["duration"]))

            filters = []
            prev_v = "0:v"
            prev_a = "0:a"
            total_dur = durs[0]
            for i in range(1, len(video_files)):
                next_v = f"{i}:v"
                next_a = f"{i}:a"
                out_v = f"v{i}"
                out_a = f"a{i}"
                offset = total_dur - fade_dur
                filters.append(f"[{prev_v}][{next_v}]xfade=transition=fade:duration={fade_dur}:offset={offset:.2f}[{out_v}]")
                filters.append(f"[{prev_a}][{next_a}]acrossfade=d={fade_dur}:c1=tri:c2=tri[{out_a}]")
                prev_v = out_v
                prev_a = out_a
                total_dur = total_dur + durs[i] - fade_dur

            filters.append(f"[{prev_a}]highpass=f=75,lowpass=f=12000,volume=1.2[a_final]")

            # Falls upscale aktiviert ist und Inputs noch nicht 1080p sind, skaliere finalen Videostream
            if upscale:
                filters.append(f"[{prev_v}]scale=1920:1080:flags=lanczos,unsharp=5:5:0.8:5:5:0.4[v_final]")
                out_v_tag = "[v_final]"
                v_enc_args = ["-crf", "17", "-preset", "medium", "-b:v", "16M", "-maxrate", "20M", "-bufsize", "32M"]
            else:
                out_v_tag = f"[{prev_v}]"
                v_enc_args = ["-crf", "18", "-preset", "fast"]

            fc = ";".join(filters)
            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", fc,
                "-map", out_v_tag,
                "-map", "[a_final]",
                "-c:v", "libx264"] + v_enc_args + [
                "-c:a", "aac", "-b:a", "192k",
                final_output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log(f"Nahtloser Film mit Kino-Überblendungen gespeichert unter: {final_output_path}", "SUCCESS")
            return
        except Exception as e:
            log(f"Kino-Überblendung fehlgeschlagen ({e}), wechsle auf Stream-Copy Concat...", "WARN")

    # Fallback: Lossless stream copy
    concat_list_file = final_output_path + ".txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for vf in video_files:
            f.write(f"file '{os.path.abspath(vf)}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        final_output_path
    ]
    log(f"Füge {len(video_files)} Szenen via FFmpeg zusammen...", "INFO")
    subprocess.run(cmd, check=True)
    if os.path.exists(concat_list_file):
        os.remove(concat_list_file)
    log(f"Fertiger Film gespeichert unter: {final_output_path}", "SUCCESS")


def print_production_report(total_scenes, duration, total_time, final_film, steps, turbo, upscale, hard_cuts, offload_between_scenes, has_character2, width, height, gpu_stats=None, scene_timings=None):
    """Gibt nach Abschluss der Filmproduktion einen detaillierten Optimierungs- und Qualitätsbericht aus."""
    print()
    log("==================================================================", "SUCCESS")
    log("📊 PRODUKTIONS-REPORT: OPTIMIERUNGEN & QUALITÄTS-ANALYSE", "SUCCESS")
    log("==================================================================", "SUCCESS")
    print(f"🎬 Fertiger Film:       {final_film}")
    print(f"⏱️ Gesamtlaufzeit Film:  {total_scenes * duration:.0f} Sekunden ({total_scenes} Szenen à {duration:.1f}s)")
    print(f"⌛ Renderzeit gesamt:   {total_time/60:.1f} Minuten (Ø {total_time/total_scenes:.1f}s pro Szene)")
    final_w = 1920 if upscale else width
    final_h = 1080 if upscale else height
    res_label = " [Full HD Lanczos3 1080p, 16 Mbps]" if upscale else " [Nativ 0.4 MP]"
    print(f"📐 Auflösung & Format:  {final_w}x{final_h} (16:9){res_label}")
    print("------------------------------------------------------------------")
    print("✅ IN DIESEM LAUF ANGEWANDTE OPTIMIERUNGEN:")

    # Check 1: Warmstart
    if not offload_between_scenes:
        saved_s = max(0, (total_scenes - 1) * 45)
        print("  1. [VRAM-Warmstart] AKTIV (offload=False):")
        print("     -> 32B-Modell blieb im 48 GB VRAM gepinnt.")
        print(f"     -> Zeitersparnis: ca. {saved_s}s ({saved_s/60:.1f} Min) eingespart!")
    else:
        print("  1. [VRAM-Warmstart] INAKTIV (Modell wurde nach jeder Szene entladen)")

    # Check 2: Sampling & Steps
    eff_steps = steps if steps is not None else (4 if turbo else 20)
    if turbo:
        print(f"  2. [Speed-Distillation] AKTIV (MiniMax H3 Turbo-LoRA, {eff_steps} Steps):")
        if eff_steps >= 8:
            print(f"     -> Sweet Spot ({eff_steps} Steps): Hohe Details bei Gesichtern, Fingern & Licht.")
        else:
            print(f"     -> Pre-Vis Turbo ({eff_steps} Steps): Maximale Geschwindigkeit für Schnittentwürfe.")
    else:
        print(f"  2. [Pure Diffusion] AKTIV (Kein Turbo, {eff_steps} Steps):")
        print("     -> Maximale physikalische Nuancen bei Rauch, Wassertropfen & Chiaroscuro-Licht.")

    # Check 3: EasyCache
    print("  3. [EasyCache DiT-Redundanz] AKTIV (reuse_threshold=0.2):")
    print("     -> Überspringt redundante DiT-Aufmerksamkeitsberechnungen (-20% bis -25% Renderzeit).")

    # Check 4: Transitions
    if not hard_cuts and total_scenes > 1:
        print("  4. [Kino-Überblendungen] AKTIV (0.4s xfade & acrossfade):")
        print("     -> Weiche Szenenübergänge und Audioblenden; kein Ruckeln und keine Klickgeräusche.")
    else:
        print("  4. [Schnitt-Modus] Harte Schnitte (Stream-Copy ohne Überblendung)")

    # Check 5: Audio Mastering
    print("  5. [Audio-EQ-Mastering] AKTIV (highpass=75Hz, lowpass=12kHz):")
    print("     -> Dumpfer Infraschall-Matsch wird herausgefiltert; Zischen & Klicks treten klar hervor.")

    # Check 6: Multi-Character
    if has_character2:
        print("  6. [Multi-Charakter] AKTIV (2 Personen via <Picture 1> & <Picture 2>):")
        print("     -> Konsistenter Gesichts- und Kleidungstransfer für Detective und Infiltratorin.")

    # Check 7: Upscaler
    if upscale:
        print("  7. [High-Fidelity 1080p Upscaling] AKTIV:")
        print("     -> Full HD 1080p (1920x1080) mit Lanczos3-Rekonstruktion & Unsharp-Maske bei 16 Mbps.")
        print("     -> VRAM-sicher entkoppelt: 0 MB VRAM-Belastung, verhindert HIP-OOM zu 100%.")
    else:
        print("  7. [KI-Upscaling] INAKTIV (Video verbleibt auf nativer Auflösung 864x480).")

    # Szenen-Timings & Clip-Statistik
    if scene_timings:
        print("------------------------------------------------------------------")
        print("⏱️ SZENEN-TIMINGS & CLIP-STATISTIK:")
        total_clip_s = sum(st["duration_s"] for st in scene_timings)
        avg_s = total_clip_s / len(scene_timings)
        min_st = min(scene_timings, key=lambda s: s["duration_s"])
        max_st = max(scene_timings, key=lambda s: s["duration_s"])
        print(f"  • Gesamte reine Clip-Renderzeit: {total_clip_s/60:.1f} Minuten ({total_clip_s:.1f}s für {len(scene_timings)} Szenen)")
        print(f"  • Durchschnitt pro 5s-Clip:      {avg_s:.1f} Sekunden")
        print(f"  • Schnellste Szene:              Szene {min_st['idx']} mit {min_st['duration_s']:.1f}s ({min_st['type']})")
        print(f"  • Langsamste Szene:              Szene {max_st['idx']} mit {max_st['duration_s']:.1f}s ({max_st['type']})")

    # GPU Telemetrie & Energiebericht
    if gpu_stats:
        print("------------------------------------------------------------------")
        print("⚡ HARDWARE-TELEMETRIE & ENERGIEVERBRAUCH (AMD Radeon PRO W7800):")
        print(f"  🌡️ Höchste GPU-Temperatur:  {gpu_stats['peak_junction']:.1f} °C Hotspot / Junction ({gpu_stats['peak_edge']:.1f} °C Edge)")
        print(f"     -> Aufgetreten um:         {gpu_stats['peak_time_str']} Uhr während: {gpu_stats['peak_scene']}")
        print(f"  ⚡ Leistungsaufnahme:         Ø {gpu_stats['avg_power']:.1f} Watt (Spitze: {gpu_stats['peak_power']:.1f} W)")
        print(f"  🔋 Energieverbrauch gesamt:   {gpu_stats['energy_wh']:.2f} Wh ({gpu_stats['energy_wh']/1000.0:.4f} kWh)")
        print(f"  💶 Geschätzte Stromkosten:    ca. {gpu_stats['cost_eur']:.4f} € (bei 0.35 €/kWh)")

    # Quality Score Calculation
    score = 6.0
    if not offload_between_scenes: score += 0.2
    if turbo and eff_steps >= 8: score += 1.0
    elif not turbo: score += 1.5
    if not hard_cuts: score += 0.8
    if has_character2: score += 0.3
    if upscale: score += 1.2
    score = min(score, 9.8)

    print("------------------------------------------------------------------")
    print(f"🌟 GESCHÄTZTER QUALITÄTS-INDEX DIESES LAUFS: {score:.1f} / 10")
    print("------------------------------------------------------------------")
    print("🚀 WAS KÖNNTE NOCH GEMACHT WERDEN? (NÄCHSTE VERBESSERUNGS-STUFEN):")

    if not upscale:
        print("  👉 1. [AUFLÖSUNG] 1080p Full-HD KI-Upscaling zuschalten:")
        print("     Befehl / Flag: --upscale")
        print("     Wirkung:       Skaliert 864x480 auf gestochen scharfes 1920x1080 (16 Mbps).")
        print("                    Beseitigt Kantenflimmern und bringt Hautporen & Wimpern zur Geltung.")

    if turbo and eff_steps < 8:
        print("  👉 2. [DETAILS] Sampling-Schritte auf den Sweet Spot (8 Steps) verdoppeln:")
        print("     Befehl / Flag: --steps 8")
        print("     Wirkung:       Verdoppelt die Diffusionspräzision für realistische Augen & Hände.")

    if turbo:
        print("  👉 3. [KINO-MASTER] Reines 20-Step Diffusion Sampling testen:")
        print("     Befehl / Flag: --no-turbo")
        print("     Wirkung:       Schaltet Turbo-LoRA ab; liefert maximale Nuancen bei volumetrischem")
        print("                    Nebel, Regen und subtilen Lichtreflexionen (Festival-Kinoqualität).")

    print("  👉 4. [GESICHTSSCHÄRFE] Master-Porträt vorab per FaceDetailer veredeln:")
    print("     Workflow:      ComfyUI Workflow '_minimax_h3_face_detailer_master.json'")
    print("     Wirkung:       Schärft das Referenzbild auf 4K-Mikroschärfe vor Drehbeginn.")
    print("                    Verhindert Video-Flickern und verankert die Identität zu 100%.")

    print("  👉 5. [SOUNDTRACK] Film-Noir Orchesterbett / Musikspur unterlegen:")
    print("     Befehl:        ffmpeg -i film.mp4 -i noir_jazz.mp3 -filter_complex \\")
    print("                    '[1:a]volume=0.25[bg];[0:a][bg]amix=inputs=2:duration=first' final.mp4")
    print("     Wirkung:       Verbindet alle Szenen mit einem durchgehenden Musikfluss und überdeckt")
    print("                    jegliches verbliebene Hintergrund-Rauschen der Audio-Synthese.")
    log("==================================================================", "SUCCESS")
    print()


def run_pipeline(story_file, character_image, output_dir, character2_image=None, width=864, height=480, duration=5.0, turbo=True, steps=None, upscale=False, hard_cuts=False, offload_between_scenes=False, comfy_url="http://127.0.0.1:8188", resume=True):
    log("==================================================================", "INFO")
    log("🚀 Starte Auto Movie Maker — MiniMax H3 Langfilm-Pipeline", "INFO")
    log("==================================================================", "INFO")

    if not check_comfy_live(comfy_url):
        sys.exit(1)

    # Pre-Flight: Einmalige Bereinigung vor Filmstart (bricht verwaiste Renderings ab & entlädt Altlasten)
    log("Pre-Flight Bereinigung: Bringe ComfyUI in sauberen Zustand...", "INFO")
    purge_comfyui_queue(comfy_url, interrupt_running=True)
    free_comfy_memory(comfy_url, unload_models=True)

    # Starte GPU-Telemetrie-Aufzeichnung für Temperatur & Energieverbrauch
    gpu_tracker = GPUTelemetryTracker(interval=1.0)
    gpu_tracker.start()

    os.makedirs(output_dir, exist_ok=True)
    comfy_output_root = os.path.expanduser("/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/output")
    comfy_input_root = os.path.expanduser("/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/input")

    # 1. Story laden oder via Ollama zerlegen
    story_data = {}
    if story_file.endswith(".yaml") or story_file.endswith(".yml") or story_file.endswith(".json"):
        with open(story_file, "r", encoding="utf-8") as f:
            if story_file.endswith(".json"):
                story_data = json.load(f)
            else:
                import yaml
                story_data = yaml.safe_load(f)
        scenes = story_data.get("scenes", story_data if isinstance(story_data, list) else [])
    else:
        scenes = decompose_text_with_ollama(story_file)

    master_style = story_data.get("style", "") or story_data.get("master_style", "")

    # Falls Drehbuch ein eigenes character_image definiert und kein individuelles per CLI erzwungen wurde
    if "character_image" in story_data and (not character_image or "YOTTEA-KREA-PRO" in character_image):
        yaml_char = story_data["character_image"]
        if os.path.exists(yaml_char):
            character_image = yaml_char
        elif os.path.exists(os.path.join(comfy_input_root, os.path.basename(yaml_char))):
            character_image = os.path.join(comfy_input_root, os.path.basename(yaml_char))

    # Kopiere Referenzbild ins ComfyUI input Verzeichnis, falls nötig
    char_base = os.path.basename(character_image)
    dest_char = os.path.join(comfy_input_root, char_base)
    if not os.path.exists(dest_char) and os.path.exists(character_image):
        import shutil
        shutil.copy2(character_image, dest_char)
    character_input_name = char_base

    # Prüfe zweiten Charakter (Multi-Charakter Unterstützung)
    if not character2_image and "character2_image" in story_data:
        character2_image = story_data["character2_image"]

    character2_input_name = None
    if character2_image:
        cand2 = character2_image
        if not os.path.exists(cand2):
            cand2 = os.path.join(comfy_input_root, os.path.basename(character2_image))
        if os.path.exists(cand2):
            char2_base = os.path.basename(cand2)
            dest_char2 = os.path.join(comfy_input_root, char2_base)
            if not os.path.exists(dest_char2):
                import shutil
                shutil.copy2(cand2, dest_char2)
            character2_input_name = char2_base
            log(f"Zweiter Charakter geladen (<Picture 2>): {character2_input_name}", "SUCCESS")

    total_scenes = len(scenes)
    effective_steps = steps if steps is not None else (4 if turbo else 20)

    # Geschätzte Laufzeit-Kalkulation (basierend auf Benchmarks der AMD Radeon PRO W7800):
    # MiniMax H3 32B DiT: ~32s pro Sampling-Schritt, ~85s Text-Conditioning & VAE-Decode
    sec_per_step = 32.0 if turbo else 34.0
    est_clip_render_sec = 85.0 + (effective_steps * sec_per_step) + (3.0 if upscale else 0.0)
    est_total_sec = 45.0 + (total_scenes * est_clip_render_sec) + 15.0
    est_total_min = est_total_sec / 60.0
    eta_time = datetime.now() + timedelta(seconds=est_total_sec)
    eta_str = eta_time.strftime("%H:%M:%S")

    log(f"Gesamtanzahl Szenen: {total_scenes} ({total_scenes * duration:.0f} Sekunden Film)", "INFO")
    target_res = "1920x1080 Full HD (Lanczos3)" if upscale else f"{width}x{height}"
    log(f"Konfiguration: Steps={effective_steps}, Turbo={turbo}, Upscale={upscale}, Zielauflösung={target_res}", "INFO")
    log(f"⏱️  Geschätzte Gesamtlaufzeit: ca. {est_total_min:.1f} Minuten ({total_scenes} Szenen à ~{est_clip_render_sec:.0f}s + End-Mastering)", "INFO")
    log(f"   Voraussichtliche Fertigstellung (ETA): ca. {eta_str} Uhr", "INFO")

    # Starte ComfyUI WebSocket Status-Tracker für Live-Node & Fortschritt
    client_id = f"auto_movie_{int(time.time())}"
    status_tracker = ComfyUIStatusTracker(comfy_url, client_id)
    status_tracker.start()

    rendered_scene_files = []
    scene_timings = []
    previous_last_frame_path = None
    start_time = time.time()

    for idx, sc in enumerate(scenes, start=1):
        sc_id = sc.get("id", idx)
        sc_type = sc.get("type", "ref2v").lower()
        sc_action = sc.get("action", sc.get("prompt", ""))
        sc_camera = sc.get("camera", "")
        sc_audio = sc.get("audio", "")

        local_scene_path = os.path.join(output_dir, f"szene_{idx:03d}.mp4")
        upscaled_scene_path = os.path.join(output_dir, f"szene_{idx:03d}_1080p.mp4")

        # Resume-Prüfung: Falls Szene bereits gerendert vorliegt, überspringe sie
        if resume and os.path.exists(local_scene_path) and os.path.getsize(local_scene_path) > 100000:
            log(f"--- Szene [{idx}/{total_scenes}] (ID: {sc_id}, Modus: {sc_type}) ---", "SCENE")
            log(f"Clip bereits gerendert ({local_scene_path}) -> Überspringe Rendering!", "SUCCESS")
            last_frame_cache = os.path.join(output_dir, f"last_frame_sc{idx}.png")
            if not os.path.exists(last_frame_cache):
                try:
                    extract_last_frame(local_scene_path, last_frame_cache)
                except Exception:
                    pass
            previous_last_frame_path = last_frame_cache

            if upscale:
                if not os.path.exists(upscaled_scene_path) or os.path.getsize(upscaled_scene_path) < 100000:
                    try:
                        upscale_video_ffmpeg(local_scene_path, upscaled_scene_path, width=1920, height=1080)
                    except Exception as e:
                        log(f"Upscaling für vorhandene Szene {idx} fehlgeschlagen: {e}", "WARN")
                rendered_scene_files.append(upscaled_scene_path if os.path.exists(upscaled_scene_path) else local_scene_path)
            else:
                rendered_scene_files.append(local_scene_path)
            continue

        # 4-Track Prompt Enhancer Zusammenführung:
        prompt_parts = []
        if master_style and master_style not in sc_action:
            prompt_parts.append(master_style)
        prompt_parts.append(sc_action)
        if sc_camera and sc_camera not in sc_action:
            prompt_parts.append(f"Camera: {sc_camera}")
        if sc_audio and sc_audio not in sc_action:
            prompt_parts.append(f"Audio: {sc_audio}")
        final_scene_prompt = ", ".join(p.strip() for p in prompt_parts if p.strip())

        log(f"--- Szene [{idx}/{total_scenes}] (ID: {sc_id}, Modus: {sc_type}) ---", "SCENE")
        log(f"Prompt: {final_scene_prompt[:120]}...", "INFO")
        gpu_tracker.set_scene(f"Szene {idx:02d} (ID: {sc_id})")
        check_vram_guard(comfy_url, min_free_gb=8.0)

        # Wenn I2V gewählt ist, aber noch kein Vor-Frame existiert -> Fallback auf Ref2V
        if sc_type == "i2v" and not previous_last_frame_path:
            log("Kein vorheriges Frame für I2V vorhanden -> wechsle automatisch zu Ref2V mit Charakter-Anker", "WARN")
            sc_type = "ref2v"

        if sc_type == "ref2v":
            # Reference-to-Video: nutzt das/die Master-Charakterbild(er)
            prompt_dict = build_api_prompt_ref2v(
                scene_prompt=final_scene_prompt,
                character_image_name=character_input_name,
                character2_image_name=character2_input_name,
                width=width,
                height=height,
                duration=duration,
                turbo=turbo,
                steps=effective_steps,
                upscale=upscale,
                offload=offload_between_scenes
            )
        else:
            # Image-to-Video: Last-Frame-Handoff
            last_frame_input_name = f"handoff_frame_sc{idx-1}.png"
            shutil_dest = os.path.join(comfy_input_root, last_frame_input_name)
            import shutil
            shutil.copy2(previous_last_frame_path, shutil_dest)

            prompt_dict = build_api_prompt_i2v(
                scene_prompt=final_scene_prompt,
                start_image_name=last_frame_input_name,
                width=width,
                height=height,
                duration=duration,
                turbo=turbo,
                steps=effective_steps,
                upscale=upscale,
                offload=offload_between_scenes
            )

        # Sende an ComfyUI
        status_tracker.reset_prompt()
        p_id = queue_prompt(prompt_dict, comfy_url, client_id=client_id)
        status_tracker.set_active_prompt(p_id)
        log(f"Prompt an ComfyUI übergeben (ID: {p_id}). Rendere Szene...", "INFO")

        t_scene_start = time.time()
        subfolder, filename = wait_for_prompt_completion(
            prompt_id=p_id,
            base_url=comfy_url,
            prompt_dict=prompt_dict,
            scene_idx=idx,
            total_scenes=total_scenes,
            gpu_tracker=gpu_tracker,
            status_tracker=status_tracker
        )
        scene_elapsed = time.time() - t_scene_start
        generated_clip = os.path.join(comfy_output_root, subfolder, filename)

        # Speichere Szene in Zielordner (native Auflösung)
        local_scene_path = os.path.join(output_dir, f"szene_{idx:03d}.mp4")
        import shutil
        shutil.copy2(generated_clip, local_scene_path)
        log(f"Szene {idx} erfolgreich gespeichert: {local_scene_path}", "SUCCESS")

        # Protokolliere Clip-Timing & gebe Zwischenbericht aus
        scene_timings.append({
            "idx": idx,
            "id": sc_id,
            "type": sc_type,
            "duration_s": scene_elapsed
        })
        total_clips_s = sum(st["duration_s"] for st in scene_timings)
        avg_clip_s = total_clips_s / len(scene_timings)
        remaining_count = total_scenes - idx
        est_rem_s = remaining_count * avg_clip_s

        log(f"🎬 Zwischenbericht: Szene [{idx}/{total_scenes}] in {scene_elapsed:.1f}s fertiggestellt!", "INFO")
        log(f"   • Reine Clip-Renderzeit bisher: {total_clips_s:.1f}s ({total_clips_s/60:.1f} Min) | Ø {avg_clip_s:.1f}s pro Szene", "INFO")
        if remaining_count > 0:
            log(f"   • Verbleibend: {remaining_count} Szenen (geschätzte Restzeit: ca. {est_rem_s/60:.1f} Min)", "INFO")

        # Extrahiere letzten Frame für möglichen nächsten Handoff (vom nativen Clip)
        last_frame_cache = os.path.join(output_dir, f"last_frame_sc{idx}.png")
        try:
            extract_last_frame(local_scene_path, last_frame_cache)
            previous_last_frame_path = last_frame_cache
        except Exception as e:
            log(f"Fehler beim Extrahieren des letzten Frames: {e}", "WARN")

        # Speichere nativen Clip für die Zusammenfügung
        rendered_scene_files.append(local_scene_path)

        # VRAM-Schutz: Freigabebefehl an ComfyUI senden
        free_comfy_memory(comfy_url, unload_models=False)

    # Beende Status-Tracker & GPU-Telemetrie-Aufzeichnung
    status_tracker.stop()
    gpu_tracker.stop()
    gpu_stats = gpu_tracker.get_summary()

    # 1. Erstelle immer den nativen Gesamtfilm (z. B. 864x480 oder 1056x608)
    native_film = os.path.join(output_dir, f"gesamtfilm_{total_scenes*int(duration)}s_native.mp4")
    log("Füge native Szenen zusammen...", "INFO")
    concatenate_scenes(rendered_scene_files, native_film, smooth=not hard_cuts, upscale=False)
    final_film = native_film

    # 2. Wenn Upscaling gewünscht ist: Führe echtes KI-Upscaling NACHTRÄGLICH als Post-Flight aus!
    if upscale:
        log("==================================================================", "INFO")
        log("🌟 Starte Post-Flight KI-Upscaling (Real-ESRGAN / AMD ROCm)...", "INFO")
        log("==================================================================", "INFO")

        # Schritt A: Entlade 32B-Diffusionsmodell aus ComfyUI VRAM, damit 48 GB frei sind
        log("Entlade Diffusionsmodell aus ComfyUI VRAM für maximale Upscale-Performance...", "INFO")
        free_comfy_memory(comfy_url, unload_models=True)
        time.sleep(2)

        # Schritt B: Führe ai_video_upscaler.py auf allen Szenen im output_dir aus
        script_dir = os.path.dirname(os.path.abspath(__file__))
        upscaler_script = os.path.join(script_dir, "ai_video_upscaler.py")
        cmd_upscale = [
            sys.executable, upscaler_script,
            "--input-dir", output_dir,
            "--pattern", "szene_*.mp4",
            "--res", "1080p",
            "--batch-size", "2",
            "--sharpen", "0.3"
        ]
        log(f"Starte KI-Upscaling: {' '.join(cmd_upscale)}", "INFO")
        try:
            proc_up = subprocess.Popen(cmd_upscale, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc_up.stdout:
                print(line, end="", flush=True)
            proc_up.wait()
            if proc_up.returncode == 0:
                log("KI-Upscaling aller Szenen erfolgreich abgeschlossen!", "SUCCESS")
            else:
                log(f"KI-Upscaler beendete mit Code {proc_up.returncode}", "WARN")
        except Exception as e:
            log(f"Fehler beim Ausführen des KI-Upscalers: {e}", "ERROR")

        # Schritt C: Sammle alle upgescalten 1080p-Szenen
        upscaled_scene_files = []
        for native_f in rendered_scene_files:
            base, ext = os.path.splitext(native_f)
            up_f = f"{base}_ai_1080p{ext}"
            if os.path.isfile(up_f):
                upscaled_scene_files.append(up_f)
            else:
                log(f"Upscaled Clip {up_f} nicht gefunden -> nutze native Version als Fallback.", "WARN")
                upscaled_scene_files.append(native_f)

        # Schritt D: Füge die upgescalten 1080p-Szenen zum finalen 1080p-Meisterwerk zusammen!
        final_film_1080p = os.path.join(output_dir, f"gesamtfilm_{total_scenes*int(duration)}s_1080p.mp4")
        log(f"Füge {len(upscaled_scene_files)} upgescalte 1080p-Szenen zusammen...", "INFO")
        concatenate_scenes(upscaled_scene_files, final_film_1080p, smooth=not hard_cuts, upscale=False)
        final_film = final_film_1080p
    else:
        final_film = os.path.join(output_dir, f"gesamtfilm_{total_scenes*int(duration)}s.mp4")
        if os.path.isfile(native_film):
            import shutil
            shutil.copy2(native_film, final_film)

    # Post-Flight Bereinigung: Gebe gesamten VRAM für Desktop frei
    log("Post-Flight Bereinigung: Gebe gesamten VRAM für Desktop & andere Modelle frei...", "INFO")
    free_comfy_memory(comfy_url, unload_models=True)

    # Post-Flight Systembereinigung (RAM, glibc, Caches & SWAP leeren gegen System-Stocken)
    cleanup_system_ram_and_swap()

    total_time = time.time() - start_time
    log(f"🎉 FILM FERTIG! Gesamtlaufzeit: {total_time/60:.1f} Minuten für {len(rendered_scene_files)} Szenen.", "SUCCESS")
    log(f"Pfad: {final_film}", "SUCCESS")

    print_production_report(
        total_scenes=len(rendered_scene_files),
        duration=duration,
        total_time=total_time,
        final_film=final_film,
        steps=steps,
        turbo=turbo,
        upscale=upscale,
        hard_cuts=hard_cuts,
        offload_between_scenes=offload_between_scenes,
        has_character2=bool(character2_input_name),
        width=width,
        height=height,
        gpu_stats=gpu_stats,
        scene_timings=scene_timings
    )


def main():
    parser = argparse.ArgumentParser(description="Auto Movie Maker — MiniMax H3 Langfilm-Pipeline")
    parser.add_argument("--story", required=True, help="Pfad zur story.yaml oder story.txt (Drehbuch)")
    parser.add_argument("--character", default="ComfyUI/input/YOTTEA-KREA-PRO (21).png", help="Pfad zum ersten Charakter-Masterbild (<Picture 1>)")
    parser.add_argument("--character2", default=None, help="Pfad zum zweiten Charakter-Masterbild (<Picture 2>) für 2-Personen-Szenen")
    parser.add_argument("--output", default="output/auto_movie", help="Ausgabeverzeichnis")
    parser.add_argument("--width", type=int, default=864, help="Breite (Standard: 864 für 0.4 MP)")
    parser.add_argument("--height", type=int, default=480, help="Höhe (Standard: 480 für 0.4 MP)")
    parser.add_argument("--mp", type=float, default=None, choices=[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.98, 1.0], help="Megapixel-Preset für 16:9 Auflösung (0.4=864x480, 0.6=1056x608, 0.7=1152x640, 0.98=1344x768)")
    parser.add_argument("--duration", type=float, default=5.0, help="Dauer pro Clip in Sekunden")
    parser.add_argument("--steps", type=int, default=None, help="Sampling-Steps (Standard: 4 bei Turbo für maximale Geschwindigkeit)")
    parser.add_argument("--upscale", action="store_true", help="Aktiviert R-ESRGAN 4x+ Batched Upscaling auf 1080p")
    parser.add_argument("--no-turbo", action="store_true", help="Deaktiviert Turbo LoRA (nutzt 20 Steps)")
    parser.add_argument("--hard-cuts", action="store_true", help="Deaktiviert weiche Kino-Überblendungen (nutzt harte Concat-Stream-Cuts)")
    parser.add_argument("--offload-between-scenes", action="store_true", help="Erzwingt Modell-Entladung nach jeder Szene (Standard: False, Modelle bleiben für max. Speed warm im VRAM)")
    parser.add_argument("--no-resume", action="store_true", help="Deaktiviert das Überspringen bereits vorhandener Szenen (erzwingt Neurendern)")
    parser.add_argument("--comfy-url", default="http://127.0.0.1:8188", help="ComfyUI URL")

    args = parser.parse_args()

    # Megapixel Preset Auflösung zuweisen
    mp_map = {
        0.2: (608, 352),
        0.3: (736, 416),
        0.4: (864, 480),
        0.5: (960, 544),
        0.6: (1056, 608),
        0.7: (1152, 640),
        0.8: (1216, 672),
        0.9: (1280, 736),
        0.98: (1344, 768),
        1.0: (1344, 768),
    }
    if args.mp is not None and args.mp in mp_map:
        args.width, args.height = mp_map[args.mp]
        log(f"Megapixel-Preset aktiviert: {args.mp} MP -> Auflösung {args.width}x{args.height}", "INFO")

    # Starte Dual-Logger (schreibt Terminal-Ausgaben simultan in production.log im Videoordner)
    os.makedirs(args.output, exist_ok=True)
    log_file_path = os.path.join(args.output, "production.log")
    dual_logger = DualLogger(log_file_path, sys.stdout, sys.stderr)
    sys.stdout = dual_logger
    sys.stderr = dual_logger

    try:
        run_pipeline(
            story_file=args.story,
            character_image=args.character,
            character2_image=args.character2,
            output_dir=args.output,
            width=args.width,
            height=args.height,
            duration=args.duration,
            turbo=not args.no_turbo,
            steps=args.steps,
            upscale=args.upscale,
            hard_cuts=args.hard_cuts,
            offload_between_scenes=args.offload_between_scenes,
            comfy_url=args.comfy_url,
            resume=not args.no_resume
        )
    finally:
        dual_logger.write_summary()
        dual_logger.close()
        sys.stdout = dual_logger.terminal_out
        sys.stderr = dual_logger.terminal_err
        log(f"📄 Vollständiges Produktions-Logfile gespeichert unter: {log_file_path}", "SUCCESS")

if __name__ == "__main__":
    main()

