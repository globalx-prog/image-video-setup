#!/usr/bin/env python3
"""
=============================================================================
📊 list_installed_models.py
Zentrale Übersicht aller installierten LLM- und ComfyUI-Modelle sowie LoRAs
=============================================================================
Funktionen:
1. 🦙 Ollama LLM-Modelle (Größe, Quantisierung, Parameter, aktiver Status)
2. 🎨 ComfyUI Diffusions-, Checkpoint-, Text-Encoder-, VAE- & Hilfsmodelle
3. 🎛️ LoRAs inklusive Abgleich mit den aktiven Workflows (Verwendungsnachweis)
4. 💾 Speicherplatz & Hardware-Auslastung (VRAM / RAM)
=============================================================================
"""

import json
import os
import shutil
import sys
import urllib.request
import urllib.error

# Pfadkonfiguration
ROOT_DIR = "/home/clemi/Projekte/LLM"
COMFY_DIR = os.path.join(ROOT_DIR, "image-video-setup/ComfyUI")
MODELS_DIR = os.path.join(COMFY_DIR, "models")
WORKFLOWS_DIR = os.path.join(COMFY_DIR, "user/default/workflows")
OLLAMA_API_TAGS = "http://127.0.0.1:11434/api/tags"
OLLAMA_API_PS = "http://127.0.0.1:11434/api/ps"
OLLAMA_STORAGE_DIRS = ["/home/models", "/usr/share/ollama/.ollama/models", os.path.expanduser("~/.ollama/models")]

# ANSI Farben
BOLD = "\033[1m"
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_bytes(num_bytes):
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 ** 2:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 ** 3:
        return f"{num_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{num_bytes / (1024 ** 3):.2f} GB"


def get_system_memory():
    mem_info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = int(parts[1].strip().split()[0]) * 1024
        total_ram = mem_info.get("MemTotal", 0)
        avail_ram = mem_info.get("MemAvailable", 0)
        used_ram = total_ram - avail_ram
        swap_total = mem_info.get("SwapTotal", 0)
        swap_free = mem_info.get("SwapFree", 0)
        swap_used = swap_total - swap_free
        return total_ram, used_ram, avail_ram, swap_total, swap_used
    except Exception:
        return 0, 0, 0, 0, 0


def print_header(title, icon="🔍"):
    print("\n" + "=" * 80)
    print(f" {icon}  {BOLD}{title}{RESET}")
    print("=" * 80)


def print_section(title, icon="📁"):
    print(f"\n{BOLD}{icon} {title}{RESET}")
    print("-" * 80)


def scan_ollama_models():
    print_header("1. OLLAMA LLM-MODELLE (/home/models / API)", icon="🦙")

    running_models = set()
    # Prüfe aktuell im RAM/VRAM geladene Modelle
    try:
        req = urllib.request.Request(OLLAMA_API_PS, headers={"User-Agent": "ModelScanner/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("models", []):
                running_models.add(m.get("name", ""))
    except Exception:
        pass

    models = []
    # Versuche über Ollama API abzufragen
    api_online = False
    try:
        req = urllib.request.Request(OLLAMA_API_TAGS, headers={"User-Agent": "ModelScanner/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("models", [])
            api_online = True
    except Exception:
        pass

    if api_online and models:
        total_size = sum(m.get("size", 0) for m in models)
        print(f"  {GREEN}● Ollama-Dienst ist AKTIV (Port 11434){RESET} | Installierte Modelle: {BOLD}{len(models)}{RESET} ({format_bytes(total_size)})\n")

        print(f"  {BOLD}{'Modellname':<30} {'Größe':<11} {'Parameter':<11} {'Quant':<9} {'Status':<15}{RESET}")
        print("  " + "─" * 78)

        for m in sorted(models, key=lambda x: x.get("name", "")):
            name = m.get("name", "unbekannt")
            size_str = format_bytes(m.get("size", 0))
            details = m.get("details", {})
            param_size = details.get("parameter_size", "k.A.")
            quant = details.get("quantization_level", "k.A.")
            family = details.get("family", "")

            if name in running_models:
                status_str = f"{GREEN}⚡ GELADEN{RESET}"
            else:
                status_str = f"{DIM}inaktiv{RESET}"

            extra_info = []
            if family:
                extra_info.append(f"Architektur: {family}")
            ctx = details.get("context_length")
            if ctx:
                extra_info.append(f"Max-Ctx: {ctx//1024}k")

            extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
            print(f"  {CYAN}{name:<30}{RESET} {size_str:<11} {param_size:<11} {quant:<9} {status_str:<15}{DIM}{extra_str}{RESET}")

    else:
        print(f"  {YELLOW}ℹ️ Ollama API offline — Durchsuche Dateisystem-Manifeste...{RESET}\n")
        manifest_found = False
        for base_dir in OLLAMA_STORAGE_DIRS:
            man_dir = os.path.join(base_dir, "manifests")
            if os.path.exists(man_dir):
                manifest_found = True
                print(f"  Verzeichnis: {base_dir}")
                for root, _, files in os.walk(man_dir):
                    for f in files:
                        rel = os.path.relpath(os.path.join(root, f), man_dir)
                        full_p = os.path.join(root, f)
                        size_kb = os.path.getsize(full_p) / 1024
                        print(f"    • {CYAN}{rel}{RESET} ({size_kb:.1f} KB Manifest)")
        if not manifest_found:
            print(f"  {RED}Keine Ollama-Manifeste gefunden.{RESET}")


def scan_workflow_lora_references():
    """Scannt alle JSON-Workflows nach verwendeten LoRAs."""
    lora_usage = {}
    if not os.path.exists(WORKFLOWS_DIR):
        return lora_usage

    for root, _, files in os.walk(WORKFLOWS_DIR):
        for f in files:
            if f.endswith(".json"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, WORKFLOWS_DIR)
                try:
                    with open(full_path, "r", encoding="utf-8") as wf:
                        data = json.load(wf)
                        nodes = data.get("nodes", [])
                        for node in nodes:
                            ntype = node.get("type", "").lower()
                            if "lora" in ntype:
                                vals = node.get("widgets_values", [])
                                if isinstance(vals, list) and len(vals) > 0:
                                    lora_name = str(vals[0])
                                    if lora_name.endswith(".safetensors") or lora_name.endswith(".pth"):
                                        if lora_name not in lora_usage:
                                            lora_usage[lora_name] = []
                                        lora_usage[lora_name].append(rel_path)
                except Exception:
                    pass
    return lora_usage


def scan_comfyui_models():
    print_header("2. COMFYUI MODELLE (image-video-setup/ComfyUI/models)", icon="🎨")

    if not os.path.exists(MODELS_DIR):
        print(f"  {RED}ComfyUI models Ordner nicht gefunden: {MODELS_DIR}{RESET}")
        return

    # Kategorien definieren
    categories = [
        ("Diffusion Models (UNet / DiT)", "diffusion_models", "Haupt-Generierungsmodelle (Flux 2, Wan 2.1/2.2, MiniMax H3)"),
        ("Checkpoints (All-in-One)", "checkpoints", "Komplettmodelle mit integriertem CLIP und VAE (Flux 1, SDXL, SD 3.5)"),
        ("Text Encoders (CLIP / T5 / Mistral)", "text_encoders", "Sprach- und Conditioning-Modelle"),
        ("VAE (Variational Autoencoder)", "vae", "Latent-Decoder und Audio/Video-Encoder"),
        ("Clip Vision", "clip_vision", "Bildidentitäts- & Feature-Extraktoren"),
        ("ControlNet & T2I-Adapter", "controlnet", "Struktur-, Tiefen- und Posenkontrolle"),
        ("Hintergrundentfernung (RMBG)", "background_removal", "Automatisches Freistellen"),
        ("Upscaler (ESRGAN)", "upscale_models", "Auflösungsvergrößerung")
    ]

    total_comfy_bytes = 0

    for cat_name, subfolder, desc in categories:
        cat_path = os.path.join(MODELS_DIR, subfolder)
        print_section(f"{cat_name}  {DIM}[{subfolder}/]{RESET}", icon="🔹")
        print(f"  {DIM}{desc}{RESET}\n")

        if not os.path.exists(cat_path):
            print(f"  {DIM}(Ordner existiert nicht){RESET}")
            continue

        files = []
        for item in sorted(os.listdir(cat_path)):
            full_item = os.path.join(cat_path, item)
            if os.path.isfile(full_item) and not item.startswith("put_") and not item.startswith("."):
                size = os.path.getsize(full_item)
                files.append((item, size, os.path.islink(full_item)))
                total_comfy_bytes += size

        if not files:
            print(f"  {DIM}Keine Modelldateien vorhanden.{RESET}")
        else:
            cat_total = sum(s for _, s, _ in files)
            for fname, size, is_link in files:
                link_tag = f" {YELLOW}[Symlink]{RESET}" if is_link else ""
                print(f"  • {BOLD}{fname:<60}{RESET} {format_bytes(size):>9}{link_tag}")
            print("  " + "─" * 72)
            print(f"    Subtotal {cat_name}: {GREEN}{format_bytes(cat_total)}{RESET} ({len(files)} Dateien)")


def scan_loras():
    print_header("3. COMFYUI LORAS & WORKFLOW-VERWENDUNG", icon="🎛️")

    lora_dir = os.path.join(MODELS_DIR, "loras")
    if not os.path.exists(lora_dir):
        print(f"  {RED}LoRA-Ordner nicht gefunden: {lora_dir}{RESET}")
        return

    workflow_usage = scan_workflow_lora_references()

    lora_files = []
    for item in sorted(os.listdir(lora_dir)):
        full_item = os.path.join(lora_dir, item)
        if os.path.isfile(full_item) and not item.startswith("put_") and not item.startswith("."):
            size = os.path.getsize(full_item)
            lora_files.append((item, size))

    if not lora_files:
        print(f"  {DIM}Keine LoRAs im Ordner vorhanden.{RESET}")
        return

    total_lora_bytes = sum(s for _, s in lora_files)
    print(f"  Installierte LoRAs: {BOLD}{len(lora_files)}{RESET} | Gesamtgröße: {BOLD}{format_bytes(total_lora_bytes)}{RESET}\n")

    for fname, size in lora_files:
        used_in = workflow_usage.get(fname, [])
        if used_in:
            unique_wfs = sorted(list(set(used_in)))
            usage_badge = f"{GREEN}✅ VERWENDET in {len(unique_wfs)} Workflow(s){RESET}"
        else:
            usage_badge = f"{DIM}⚪ Nicht in aktiven Workflows verknüpft{RESET}"

        print(f"  • {BOLD}{fname}{RESET} ({format_bytes(size)})")
        print(f"    Status: {usage_badge}")
        if used_in:
            for wf in unique_wfs[:3]:
                print(f"     └─ {CYAN}{wf}{RESET}")
            if len(unique_wfs) > 3:
                print(f"     └─ {DIM}... und {len(unique_wfs)-3} weitere{RESET}")
        print()


def print_system_summary():
    print_header("4. HARDWARE- & SPEICHER-STATUS", icon="💾")

    total_ram, used_ram, avail_ram, swap_total, swap_used = get_system_memory()
    disk_total, disk_used, disk_free = shutil.disk_usage(ROOT_DIR)

    print(f"  {BOLD}Festplatte ({ROOT_DIR}):{RESET}")
    print(f"    Gesamt: {format_bytes(disk_total)} | Belegt: {format_bytes(disk_used)} | {GREEN}Frei: {format_bytes(disk_free)}{RESET} ({disk_free/disk_total*100:.1f} % frei)\n")

    print(f"  {BOLD}Host-Arbeitsspeicher (RAM):{RESET}")
    print(f"    Gesamt: {format_bytes(total_ram)} | Belegt: {format_bytes(used_ram)} | {GREEN}Verfügbar: {format_bytes(avail_ram)}{RESET}")
    if swap_total > 0:
        swap_color = GREEN if swap_used < 1024**3 else YELLOW
        print(f"    Swap:   {swap_color}{format_bytes(swap_used)}{RESET} von {format_bytes(swap_total)} belegt\n")

    # Service-Check
    comfy_status = f"{RED}Offline{RESET}"
    try:
        with urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=0.8) as r:
            if r.status == 200:
                comfy_status = f"{GREEN}Online (Port 8188){RESET}"
    except Exception:
        pass

    ollama_status = f"{RED}Offline{RESET}"
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.8) as r:
            if r.status == 200:
                ollama_status = f"{GREEN}Online (Port 11434){RESET}"
    except Exception:
        pass

    print(f"  {BOLD}Dienste:{RESET}")
    print(f"    ComfyUI Server: {comfy_status}")
    print(f"    Ollama Server:  {ollama_status}")
    print("=" * 80 + "\n")


def main():
    print_system_summary()
    scan_ollama_models()
    scan_comfyui_models()
    scan_loras()


if __name__ == "__main__":
    main()

