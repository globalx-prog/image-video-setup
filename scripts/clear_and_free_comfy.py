#!/usr/bin/env python3
import json
import time
import urllib.request

COMFY_URL = "http://127.0.0.1:8188"

def post_json(path, data):
    req = urllib.request.Request(
        f"{COMFY_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8")

print("1. Clearing ComfyUI queue...")
post_json("/queue", {"clear": True})
print("2. Interrupting active job...")
post_json("/interrupt", {})
time.sleep(2.0)
print("3. Requesting model unload & memory free...")
post_json("/free", {"unload_models": True, "free_memory": True})

for i in range(15):
    time.sleep(2.0)
    post_json("/interrupt", {})
    post_json("/free", {"unload_models": True, "free_memory": True})
    with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5) as r:
        st = json.loads(r.read().decode("utf-8"))
        dev = st.get("devices", [{}])[0]
        vram_used = (dev.get("vram_total", 0) - dev.get("vram_free", 0)) / (1024**3)
        ram_free = st.get("system", {}).get("ram_free", 0) / (1024**3)
        print(f"   Tick {i+1}: VRAM Used={vram_used:.1f} GiB, Host RAM Free={ram_free:.1f} GiB")
        if vram_used < 2.0 and ram_free > 35.0:
            print("Memory completely reclaimed!")
            break

