#!/usr/bin/env python3
"""
🔍 find_video_loras.py — Automatischer Online-Finder für Video-LoRAs
=============================================================================
Durchsucht Civitai und HuggingFace nach den besten und neuesten Video-LoRAs
in den Kernkategorien:
  1. 🎬 Cinematic Lighting & Chiaroscuro
  2. 🎥 Kamera-Dynamik & Movement (FPV, Whip Pan, Dolly, Orbit)
  3. 🎞️ 35mm Analogfilm & Filmkorn (Kodak, Vintage, Halation)
  4. 👤 Gesichts- & Hauttextur-Details (Skin Pores, Realism)
  5. 💥 Action, Stunts & physikalische Dynamik
  6. ⚡ Speed-Distillation (Turbo / Few-Step LoRAs)

Liefert konkrete Implementierungsempfehlungen für ComfyUI und auto_movie_maker.py!
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime

CATEGORIES = {
    "cinematic": {
        "title": "Cinematic Lighting & Chiaroscuro (Kinolicht & Schatten)",
        "icon": "🎬",
        "civitai_queries": ["cinematic lighting video", "chiaroscuro video", "cyberpunk lighting video", "noir video"],
        "hf_queries": ["cinematic-video-lora", "lighting-lora", "video-lighting"],
        "default_strength": 0.75,
        "recommended_for": "Krimis, Thriller, atmosphärische Regen- und Nachtszenen"
    },
    "camera": {
        "title": "Kamera-Dynamik & Movement (FPV, Dolly, Whip Pan)",
        "icon": "🎥",
        "civitai_queries": ["camera motion video", "drone fpv video", "dolly zoom video", "orbit camera video"],
        "hf_queries": ["camera-motion-lora", "wan2.1-camera", "camera-control-lora"],
        "default_strength": 0.80,
        "recommended_for": "Verfolgungsjagden, Hechtsprünge, dramatische Schuss-Gegenschuss Schwenks"
    },
    "grain": {
        "title": "35mm Analogfilm & Filmkorn (Kodak, Vintage Film Look)",
        "icon": "🎞️",
        "civitai_queries": ["35mm film video", "kodak portra video", "film grain video", "vintage film video"],
        "hf_queries": ["film-grain-lora", "35mm-video-lora", "kodak-lora"],
        "default_strength": 0.65,
        "recommended_for": "Beseitigt den sterilen KI-Plastik-Look; verleiht organische Körnigkeit"
    },
    "detail": {
        "title": "Gesichts- & Hauttextur-Details (Skin Pores & Facial Realism)",
        "icon": "👤",
        "civitai_queries": ["skin detail video", "face realism video", "hyper detail video", "skin texture"],
        "hf_queries": ["face-detail-video", "skin-texture-lora", "detail-tweaker"],
        "default_strength": 0.70,
        "recommended_for": "Intensive Close-Ups, emotionale Dialoge, realistische Mimik ohne Glättung"
    },
    "action": {
        "title": "Action, Stunts & physikalische Dynamik (Explosionen, Kämpfe)",
        "icon": "💥",
        "civitai_queries": ["action fight video", "explosion video", "stunt video", "dynamic motion video"],
        "hf_queries": ["action-video-lora", "wan-action-lora", "physics-lora"],
        "default_strength": 0.85,
        "recommended_for": "Kugelhagel, zersplitterndes Glas, schnelle Flucht- und Kampfszenen"
    },
    "speed": {
        "title": "Speed-Distillation (Turbo / 4-Step / 8-Step LoRAs)",
        "icon": "⚡",
        "civitai_queries": ["turbo lora video", "distill 4step video", "lightning lora video"],
        "hf_queries": ["Wan2.1-Distill-Loras", "minimax-turbo", "video-distill-lora"],
        "default_strength": 1.00,
        "recommended_for": "Verkürzt die Rechenzeit um bis zu 65% ohne Qualitätsabstriche"
    }
}


def search_civitai(query, limit=3):
    """Sucht nach LoRAs auf der Civitai API."""
    url = f"https://civitai.com/api/v1/models?types=LORA&query={urllib.parse.quote(query)}&limit={limit}&sort=Highest+Rated"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; VideoLoraFinder/1.0)"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                versions = item.get("modelVersions", [])
                latest_ver = versions[0] if versions else {}
                files = latest_ver.get("files", [])
                safetensors_file = next((f for f in files if f.get("name", "").endswith(".safetensors")), files[0] if files else {})

                results.append({
                    "source": "Civitai",
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "creator": item.get("creator", {}).get("username", "Unknown"),
                    "base_model": latest_ver.get("baseModel", "Universal / SDXL / Wan"),
                    "downloads": item.get("stats", {}).get("downloadCount", 0),
                    "rating": item.get("stats", {}).get("rating", 0.0),
                    "download_url": latest_ver.get("downloadUrl", f"https://civitai.com/models/{item.get('id')}"),
                    "filename": safetensors_file.get("name", f"lora_{item.get('id')}.safetensors"),
                    "trigger_words": latest_ver.get("trainedWords", []),
                    "page_url": f"https://civitai.com/models/{item.get('id')}"
                })
    except Exception as e:
        # Fallback wenn Offline oder Sandbox blockiert
        pass
    return results


def search_huggingface(query, limit=3):
    """Sucht nach Video-LoRAs auf der Hugging Face API."""
    url = f"https://huggingface.co/api/models?search={urllib.parse.quote(query)}&filter=lora&sort=downloads&direction=-1&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; VideoLoraFinder/1.0)"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            for item in data:
                model_id = item.get("id", "")
                results.append({
                    "source": "HuggingFace",
                    "id": model_id,
                    "name": model_id.split("/")[-1],
                    "creator": model_id.split("/")[0] if "/" in model_id else "Community",
                    "base_model": "Wan 2.1 / MiniMax / Hunyuan",
                    "downloads": item.get("downloads", 0),
                    "rating": item.get("likes", 0),
                    "download_url": f"https://huggingface.co/{model_id}",
                    "filename": f"{model_id.replace('/', '_')}.safetensors",
                    "trigger_words": [model_id.split("/")[-1].lower()],
                    "page_url": f"https://huggingface.co/{model_id}"
                })
    except Exception as e:
        pass
    return results


def run_lora_discovery(categories_to_check, output_md=None):
    print("==================================================================")
    print("🔍 VIDEO-LORA FINDER & EMPFEHLUNGS-SYSTEM")
    print("==================================================================")
    print("Durchsuche Online-Repositories (Civitai & Hugging Face)...")
    print()

    all_recommendations = {}

    for cat_key in categories_to_check:
        cat_info = CATEGORIES.get(cat_key)
        if not cat_info:
            continue

        print(f"{cat_info['icon']} KATEGORIE: {cat_info['title']}")
        print(f"   Einsatzgebiet: {cat_info['recommended_for']}")
        print(f"   Empfohlene Stärke: {cat_info['default_strength']:.2f}")

        found_items = []
        # Civitai Search
        for q in cat_info["civitai_queries"][:2]:
            found_items.extend(search_civitai(q, limit=2))
        # HuggingFace Search
        for q in cat_info["hf_queries"][:1]:
            found_items.extend(search_huggingface(q, limit=2))

        # Deduplizieren nach ID/Name
        seen = set()
        deduped = []
        for item in found_items:
            key = item["name"].lower()
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        # Sortieren nach Downloads
        deduped.sort(key=lambda x: x["downloads"], reverse=True)
        top_picks = deduped[:3]

        all_recommendations[cat_key] = {
            "info": cat_info,
            "picks": top_picks
        }

        if top_picks:
            for idx, p in enumerate(top_picks, start=1):
                trig_str = ", ".join(p['trigger_words'][:3]) if p['trigger_words'] else "Keine spezifischen Trigger nötig"
                print(f"   [{idx}] {p['name']} ({p['source']})")
                print(f"       Ersteller: {p['creator']} | Downloads: {p['downloads']:,} | Basis: {p['base_model']}")
                print(f"       Trigger-Wörter: {trig_str}")
                print(f"       Link: {p['page_url']}")
        else:
            print("   (Keine neuen API-Treffer; Offline-Modus aktiv oder Rate-Limit)")
        print()

    # Markdown Export falls gewünscht
    if output_md:
        write_markdown_report(all_recommendations, output_md)
        print(f"✅ Vollständiger Implementierungs-Leitfaden gespeichert unter: {output_md}")

    # Konkrete Implementierungs-Anleitung ausgeben
    print_implementation_guide()


def write_markdown_report(recommendations, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# 🎬 Empfohlene Video-LoRAs für Maximale Bildqualität\n\n")
        f.write("> Automatisch generiert am " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write("---\n\n")

        for cat_key, data in recommendations.items():
            info = data["info"]
            picks = data["picks"]
            f.write(f"## {info['icon']} {info['title']}\n\n")
            f.write(f"- **Optimaler Einsatzzweck:** {info['recommended_for']}\n")
            f.write(f"- **Empfohlene Stärke in ComfyUI:** `{info['default_strength']:.2f}`\n\n")

            if picks:
                f.write("| Rang | LoRA Name | Plattform | Basis-Modell | Downloads | Trigger-Keywords | Download / Info |\n")
                f.write("| :-: | :--- | :---: | :---: | :---: | :--- | :--- |\n")
                for i, p in enumerate(picks, start=1):
                    trigs = ", ".join(f"`{w}`" for w in p['trigger_words'][:2]) if p['trigger_words'] else "*Direkt aktiv*"
                    f.write(f"| **{i}** | **{p['name']}** | {p['source']} | {p['base_model']} | {p['downloads']:,} | {trigs} | [Modell ansehen]({p['page_url']}) |\n")
            else:
                f.write("*Aktuell keine Online-Treffer (Netzwerkabfrage fehlgeschlagen).*\n")
            f.write("\n---\n\n")

        f.write("## 🛠️ Wie binde ich ein neues LoRA in ComfyUI ein?\n\n")
        f.write("1. **Download:** Legen Sie die heruntergeladene `.safetensors`-Datei in folgendem Ordner ab:\n")
        f.write("   ```bash\n   /home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/loras/\n   ```\n\n")
        f.write("2. **In ComfyUI einhängen:**\n")
        f.write("   - Fügen Sie eine `LoraLoaderModelOnly` Node zwischen dem UNET-Loader (Node 1) und dem Modell-Switch (Node 6) ein.\n")
        f.write("   - Stellen Sie die Stärke (`strength_model`) auf den oben empfohlenen Wert ein (typisch `0.65` bis `0.80`).\n\n")
        f.write("3. **Im Prompt aufrufen:**\n")
        f.write("   - Fügen Sie die oben genannten Trigger-Keywords in die `action`- oder `style`-Zeile Ihres Drehbuchs ein.\n")


def print_implementation_guide():
    print("==================================================================")
    print("🛠️ WIE IMPLEMENTIERE ICH EIN NEUES LORA IN MEIN SETUP?")
    print("==================================================================")
    print("1. SPEICHERORT:")
    print("   Laden Sie die .safetensors-Datei herunter und verschieben Sie sie nach:")
    print("   -> ComfyUI/models/loras/<name>.safetensors")
    print()
    print("2. AUTOMATISCHES EINBINDEN IN auto_movie_maker.py:")
    print("   In 'build_api_prompt_ref2v' wird das LoRA einfach hinter Node 1 gekoppelt:")
    print("   graph['5'] = {")
    print("       'class_type': 'LoraLoaderModelOnly',")
    print("       'inputs': {'lora_name': '<name>.safetensors', 'strength_model': 0.75, 'model': ['1', 0]}")
    print("   }")
    print()
    print("3. REGIE-TIPP BEIM PROMPTEN:")
    print("   Beginnen Sie immer mit Stärke 0.70. Mehr als 0.90 führt oft zu harten")
    print("   Kontrastabrissen oder unnatürlichen Farbsättigungen.")
    print("==================================================================")


def main():
    parser = argparse.ArgumentParser(description="Video-LoRA Finder für MiniMax H3, Wan 2.1 & Hunyuan")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()) + ["all"], default="all", help="Kategorie filtern (Standard: all)")
    parser.add_argument("--save-markdown", default="docs/32-empfohlene-video-loras.md", help="Pfad für Markdown-Bericht")
    args = parser.parse_args()

    cats = list(CATEGORIES.keys()) if args.category == "all" else [args.category]
    run_lora_discovery(cats, output_md=args.save_markdown)


if __name__ == "__main__":
    main()

