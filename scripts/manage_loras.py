#!/usr/bin/env python3
"""
LoRA Manager & Downloader für MiniMax H3, FLUX und WAN 2.2
Analysiert vorhandene LoRAs, bewertet deren Nutzen und bietet 1-Klick-Downloads für empfohlene Ergänzungen.
"""

import os
import sys
import shutil
import urllib.request
import argparse

LORA_DIR = os.path.expanduser("/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/loras")

# Datenbank bekannter LoRAs auf deinem PC
KNOWN_LORAS = {
    "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors": {
        "model": "MiniMax H3 (DiT)",
        "type": "8-Step Turbo LoRA",
        "nutzen": "ESSENTIELL (Standard)",
        "beschreibung": "Ermöglicht 4- bis 8-Step Sampling statt 20-30 Steps. Beschleunigt H3 um das 3- bis 4-fache ohne Qualitätseinbußen."
    },
    "Flux_2-Turbo-LoRA_comfyui.safetensors": {
        "model": "FLUX.2 Dev",
        "type": "Turbo Acceleration",
        "nutzen": "SEHR HOCH (T2I)",
        "beschreibung": "Reduziert die Generierungszeit von FLUX.2 Bildern auf ca. 8 Steps. Perfekt für schnelle Charakter-Masterbilder."
    },
    "juggernaut_flux_lora.safetensors": {
        "model": "FLUX.1 / FLUX.2",
        "type": "Style & Realism",
        "nutzen": "HOCH (Porträts)",
        "beschreibung": "Erzeugt kinoreife Hauttexturen, analoge Beleuchtung und fotorealistische Gesichtszüge für Master-Keyframes."
    },
    "FireRed-Image-Edit-1.0-Lightning-8steps-v1.0.safetensors": {
        "model": "FireRed Edit",
        "type": "Image Inpainting",
        "nutzen": "SPEZIALISIERT",
        "beschreibung": "Wird für anweisungsbasierte Bildretusche und Keyframe-Inpainting in 8 Schritten genutzt."
    },
    "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors": {
        "model": "WAN 2.2 I2V 14B",
        "type": "Lightx2v 4-Step (High Noise)",
        "nutzen": "HOCH (für WAN)",
        "beschreibung": "Stufe 1 des extrem schnellen 4-Step Samplings für das alternative WAN 2.2 Videomodell."
    },
    "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors": {
        "model": "WAN 2.2 I2V 14B",
        "type": "Lightx2v 4-Step (Low Noise)",
        "nutzen": "HOCH (für WAN)",
        "beschreibung": "Stufe 2 des 4-Step Samplings für WAN 2.2 (Detailschärfung bei niedrigem Rauschen)."
    }
}

# Empfohlene LoRAs zum Nachladen
RECOMMENDED_DOWNLOADS = [
    {
        "name": "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        "url": "https://huggingface.co/Comfy-Org/MiniMax_h3_repackaged/resolve/main/split_files/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        "size_est": "~1.9 GB",
        "zweck": "MiniMax H3 Ref2V 4-Step Turbo (Ultraschnelle Charakter-Treue in unter 50s pro Clip)"
    },
    {
        "name": "flux_realism_lora.safetensors",
        "url": "https://huggingface.co/XLabs-AI/flux-RealismLora/resolve/main/lora.safetensors",
        "size_est": "~220 MB",
        "zweck": "FLUX Master-Keyframe Realismus (Fotorealistische Haut- und Fellstrukturen)"
    }
]


def check_disk_space():
    total, used, free = shutil.disk_usage("/home/clemi/Projekte/LLM")
    print("\n" + "="*70)
    print(f"💾 FESTPLATTENSPEICHER (Projekt-Partition: /home/clemi/Projekte/LLM)")
    print("="*70)
    print(f"  Gesamtgröße:    {total / (1024**3):.1f} GB")
    print(f"  Belegt:         {used / (1024**3):.1f} GB")
    print(f"  Freier Speicher: {free / (1024**3):.1f} GB ({free/total*100:.1f} % frei)")
    print("="*70 + "\n")
    return free


def analyze_installed_loras():
    print("🔍 ANALYSE DER INSTALLIERTEN LORAS:\n")
    if not os.path.exists(LORA_DIR):
        print(f"Ordner nicht gefunden: {LORA_DIR}")
        return

    found = []
    for f in sorted(os.listdir(LORA_DIR)):
        full_p = os.path.join(LORA_DIR, f)
        if os.path.isfile(full_p) and not f.startswith("put_"):
            found.append(f)

    for idx, f in enumerate(found, 1):
        full_p = os.path.join(LORA_DIR, f)
        size_mb = os.path.getsize(full_p) / (1024**2)
        info = KNOWN_LORAS.get(f, {
            "model": "Unbekannt / Custom",
            "type": "LoRA",
            "nutzen": "Prüfen",
            "beschreibung": "Benutzerdefiniertes oder externes LoRA."
        })

        print(f"[{idx}] {f}")
        print(f"    Größe:        {size_mb:.1f} MB")
        print(f"    Basis-Modell: {info['model']}")
        print(f"    Typ / Nutzen: {info['type']} | Status: {info['nutzen']}")
        print(f"    Erklärung:    {info['beschreibung']}\n")


def list_recommended():
    print("🌟 EMPFOHLENE ZUSÄTZLICHE LORAS FÜR DEIN SETUP:\n")
    for idx, r in enumerate(RECOMMENDED_DOWNLOADS, 1):
        target = os.path.join(LORA_DIR, r["name"])
        status = "✅ BEREITS INSTALLIERT" if os.path.exists(target) else "⬇️ NOCH NICHT INSTALLIERT"
        print(f"[{idx}] {r['name']} ({r['size_est']}) — {status}")
        print(f"    Zweck: {r['zweck']}")
        print(f"    Quelle: {r['url']}\n")


def download_lora(lora_idx):
    if lora_idx < 1 or lora_idx > len(RECOMMENDED_DOWNLOADS):
        print("Ungültige Auswahl!")
        return

    item = RECOMMENDED_DOWNLOADS[lora_idx - 1]
    dest = os.path.join(LORA_DIR, item["name"])
    if os.path.exists(dest):
        print(f"Datei existiert bereits: {dest}")
        return

    print(f"Lade herunter: {item['name']}...")
    try:
        urllib.request.urlretrieve(item["url"], dest)
        print(f"✅ Erfolgreich gespeichert unter: {dest}")
    except Exception as e:
        print(f"❌ Fehler beim Download: {e}")


def main():
    parser = argparse.ArgumentParser(description="LoRA Manager für MiniMax H3 & FLUX")
    parser.add_argument("--download", type=int, help="Index des empfohlenen LoRAs zum Download (1 oder 2)")
    args = parser.parse_args()

    check_disk_space()
    analyze_installed_loras()
    list_recommended()

    if args.download:
        download_lora(args.download)


if __name__ == "__main__":
    main()

