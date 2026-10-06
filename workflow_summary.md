# Dein KI Bild- & Video-Workflow (Zusammenfassung)

Dieses Dokument fasst dein aktuelles Setup für die Bild- und Videogenerierung zusammen, nachdem wir die Architektur auf deine 48GB AMD-Grafikkarte zugeschnitten haben.

---

## 🛠 Welche Tools laufen für Bild & Video?

1.  **ComfyUI (Die Engine):**
    *   **Wie es läuft:** Nativ direkt auf deinem Linux-Host, isoliert in einer modernen Python-Umgebung (`uv`).
    *   **Zweck:** Das ist der "Motor", der die eigentliche Schwerstarbeit (Berechnung auf der Grafikkarte via ROCm) übernimmt.
    *   **Starten:** Über das Skript `./start_comfyui.sh` im Ordner `image-video-setup`.
2.  **Open WebUI (Das Chat-Frontend):**
    *   **Wie es läuft:** In deinem bestehenden Docker-Setup.
    *   **Zweck:** Dient als bequeme Text-Schnittstelle, die im Hintergrund Befehle an ComfyUI sendet.

---

## 🎨 Wie und wo werden Bilder & Videos generiert?

Du hast zwei völlig verschiedene, aber jeweils hochgradig effiziente Wege:

### Weg A: Der Chat-Modus (Schnelle Bilder)
*   **Wo:** In **Open WebUI** (deiner gewohnten Oberfläche für LLMs/Ollama).
*   **Wie:** Du chattest ganz normal und sagst z. B. *"Erstelle ein fotorealistisches Bild von..."*. 
*   **Wofür:** Perfekt für Brainstorming, Konzeptkunst oder wenn du schnelle Ergebnisse brauchst, ohne dich um technische Details zu kümmern. *(Hinweis: Unterstützt aktuell primär Bilder, keine Videos).*

### Weg B: Der Pro-Modus (Videos & High-End Bilder)
*   **Wo:** Im Browser unter **`http://localhost:8188`** (ComfyUI Interface).
*   **Wie:** Über sogenannte "Workflows". Du baust die Knotenpunkte (Nodes) nicht selbst. Lade dir ein Bild/Video von [Civitai](https://civitai.com) oder [OpenArt](https://openart.ai) herunter, das in ComfyUI erstellt wurde, und ziehe es per **Drag & Drop** in den Browser. ComfyUI baut den gesamten Workflow (inklusive LTX-Video-Nodes oder FLUX-Nodes) automatisch nach. Du klickst nur noch auf "Queue Prompt".
*   **Wofür:** Videogenerierung, präzise Bildkontrolle, Upscaling auf 4K, Face-Swapping.

---

## 📥 Wie und wo werden Modelle geladen?

Da ComfyUI lokal läuft, müssen die KI-Modelle als Dateien (meist `.safetensors`) auf deiner Festplatte liegen.

### 1. Der bequeme Weg (für Videos & Standard-Modelle)
Wir haben den **ComfyUI-Manager** für dich installiert.
*   Öffne `http://localhost:8188`.
*   Klicke rechts unten auf **"Manager"**.
*   Wähle **"Install Models"**.
*   Suche hier nach Modellen (z. B. "LTX-Video") und klicke auf installieren. Der Manager lädt die riesigen Dateien herunter und legt sie exakt in den richtigen Unterordnern ab.

### 2. Der manuelle Weg (für riesige Bildmodelle wie FLUX)
Manche spezifischen Modelle (z. B. feingetunte Versionen von der Plattform Civitai) musst du manuell herunterladen.
*   **Wo ablegen?** Im Ordner: 
    `/home/clemi/Projekte/LLM/image-video-setup/ComfyUI/models/checkpoints/`
*   Sobald eine neue `.safetensors`-Datei dort liegt, klickst du in ComfyUI rechts auf **"Refresh"** und kannst das Modell aus der Dropdown-Liste auswählen.
