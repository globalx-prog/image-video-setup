# 🌀 Lüfter-Setups & Kühlprofile: Von Flüsterleise bis Dauerlast (W7800 / RDNA3)
> **Ziel:** Praxisnahe Dokumentation aller möglichen Lüfter-Konfigurationen für die **AMD Radeon PRO W7800 (48 GB)** unter Linux/ROCm – inklusive Lautstärke, Temperaturen, Befehlen und Automatisierungs-Optionen.

---

## 1. 🔍 Technische Grundlagen des W7800 Radiallüfters

Die **AMD Radeon PRO W7800** nutzt ein professionelles **Radial-Kühldesign (Blower)**. Die Luft wird im Gehäuseinneren angesaugt und mit hohem statischem Druck direkt durch die Kupfer-Lamellen über das Slotblech nach außen geblasen.

### Die zwei Temperatur-Sensoren im Vergleich:
1. **Edge-Temperatur (`temp1_input`):**  
   Misst den Rand des Silizium-Dies. Diese Temperatur liegt meist bei **55–75 °C** und ist trügerisch harmlos.
2. **Hotspot / Junction-Temperatur (`temp2_input`):**  
   Misst die heißeste Stelle der Compute-Units und des Speicher-Controllers. **Dieser Wert entscheidet über Drosselung!**
   * `< 80 °C:` Perfekt – maximale Shader-Takte (> 2.100 MHz) dauerhaft stabil.
   * `85–90 °C:` Erste automatische Takt-Reduktion um 80–120 MHz (Downbinning).
   * `> 95 °C:` Starkes Thermal-Throttling; Speicher-Takte brechen ein, um 100 °C nicht zu überschreiten.

### Warum das vBIOS ab Werk zu heiß wird:
Das Werks-vBIOS priorisiert **Akkustik im Büro**: Bis 80 °C Hotspot dreht der Lüfter nur mit ca. **20 % (PWM 51/255, ~1.100 RPM)**. Unter 233 W Diffusions-Dauerlast steigt der Hotspot dadurch schnell auf **95–98 °C**.

---

## 2. 📊 Die 5 praxiserprobten Lüfter-Profile im Vergleich

| Profil-Name | Lüfter-PWM | Drehzahl | Lautstärke | Hotspot (230W DiT) | Empfohlener Einsatzbereich |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Silent Desktop** | `30–35 %` | ~1.600 RPM | **~34 dB(A)** (flüsterleise) | 90–96 °C | Desktop-Betrieb, Code-Editing, kurze Bild-Generierung (FLUX / SDXL). |
| **2. Balanced Studio** | `50 %` | ~2.300 RPM | **~42 dB(A)** (leises Rauschen) | 80–84 °C | Angenehmes Arbeiten im selben Raum bei gelegentlichen Video-Clips. |
| **3. Production Sweet Spot** | **`65 %`** | ~3.000 RPM | **~50 dB(A)** (monotones Rauschen) | **72–76 °C** | **Standard für Langfilme (12+ Szenen):** Beseitigt Thermal Throttling komplett. |
| **4. Turbo Max-Cooling** | `85 %` | ~4.000 RPM | **~60 dB(A)** (deutlich hörbar) | **64–68 °C** | Unbeaufsichtigte Nacht-Batches, heiße Sommertage (>28 °C Raumtemp). |
| **5. vBIOS Automatik** | `Dynamisch` | variabel | variabel (anfangs sehr leise) | 92–98 °C | Werkszustand nach Systemstart. |

---

## 3. 🛠️ Sofort-Befehle über `w7800_perf_boost.sh`

Das Skript [`scripts/w7800_perf_boost.sh`](../scripts/w7800_perf_boost.sh) bietet vordefinierte Kurzbefehle:

```bash
# 1. Status prüfen (Edge, Hotspot, Watt, aktuelle Drehzahl)
./scripts/w7800_perf_boost.sh status

# 2. Performance Sweet Spot (65% Lüfter + 230W Power-Limit + COMPUTE-Profil)
sudo ./scripts/w7800_perf_boost.sh boost

# 3. Beliebigen Wunschwert in Prozent setzen (z. B. 55%):
sudo ./scripts/w7800_perf_boost.sh set-fan 55

# 4. Vordefinierte Presets wählen:
sudo ./scripts/w7800_perf_boost.sh silent        # 35% (Leise für Büro)
sudo ./scripts/w7800_perf_boost.sh balanced      # 50% (Guter Kompromiss)
sudo ./scripts/w7800_perf_boost.sh performance   # 65% (Kühl für Filmproduktion)
sudo ./scripts/w7800_perf_boost.sh max           # 85% (Maximale Kühlung)

# 5. Zurück auf Werks-Automatik (vBIOS):
sudo ./scripts/w7800_perf_boost.sh auto
```

---

## 4. 🧠 Setup A: Dynamische Hysteresen-Lüfterkurve (Daemon)

Wer nicht manuell feste Prozentwerte einstellen möchte, kann die dynamische Temperatur-Kurve nutzen. Sie pollt die Hotspot-Temperatur alle 2 Sekunden und regelt gleitend nach:

* **Hotspot < 55 °C:** 37 % PWM (leise)
* **Hotspot 55–65 °C:** 53 % PWM
* **Hotspot 65–75 °C:** 65 % PWM (Render-Sweet-Spot)
* **Hotspot 75–83 °C:** 76 % PWM
* **Hotspot > 83 °C:** 88 % PWM (Notfall-Kühlung)

### Ausführung im Terminal (Vordergrund mit Live-Anzeige):
```bash
sudo ./scripts/w7800_perf_boost.sh fan-curve
```
*(Beenden mit `Ctrl+C` schaltet den Lüfter automatisch wieder auf vBIOS-Automatik zurück).*

### Ausführung im Hintergrund (als Daemon während der Arbeit):
```bash
sudo nohup ./scripts/w7800_perf_boost.sh fan-curve > /dev/null 2>&1 &
```

---

## 5. 🔓 Setup B: Rootless Steuerung ohne `sudo` (udev-Regel)

Standardmäßig gehört die Datei `pwm1` dem Benutzer `root`. Mit einer einfachen udev-Regel können Sie dem Benutzer `clemi` dauerhaft Schreibrechte geben, sodass Lüfterbefehle **ohne Passwort** funktionieren:

### 1. udev-Regel anlegen:
Erstellen Sie `/etc/udev/rules.d/99-amdgpu-fan.rules`:
```udev
ACTION=="add", SUBSYSTEM=="hwmon", KERNEL=="hwmon*", ATTRS{name}=="amdgpu", RUN+="/bin/chmod 0666 /sys/class/drm/card1/device/hwmon/%k/pwm1 /sys/class/drm/card1/device/hwmon/%k/pwm1_enable"
```

### 2. Regel laden:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 3. Direkte Steuerung ohne sudo:
```bash
# Lüfter direkt auf 65% setzen (165 von 255):
echo 1 > /sys/class/drm/card1/device/hwmon/hwmon6/pwm1_enable
echo 165 > /sys/class/drm/card1/device/hwmon/hwmon6/pwm1

# Zurück auf Automatik:
echo 2 > /sys/class/drm/card1/device/hwmon/hwmon6/pwm1_enable
```

---

## 6. 🚀 Setup C: Dauerhafter Autostart beim Booten (systemd)

Damit die Grafikkarte nach jedem Rechnerneustart direkt mit optimalem Power-Limit (230W) und leiser, aber geschützter Kühlung läuft:

Erstellen Sie `/etc/systemd/system/w7800-boost.service`:
```ini
[Unit]
Description=AMD Radeon PRO W7800 Performance Boost & Cooling
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/home/clemi/Projekte/LLM/image-video-setup/scripts/w7800_perf_boost.sh boost
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Aktivieren mit:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now w7800-boost.service
```

---

## 7. 🎬 Setup D: On-Demand Pipeline-Steuerung (Auto-Lüfter)

Für maximalen Komfort kann die Film-Pipeline den Lüfter selbstständig regeln:
1. **Vor Filmstart:** Pipeline schaltet den Blower auf **65 %**.
2. **Während des Renderns:** Hotspot bleibt stabil bei **~74 °C** (keine Drosselung).
3. **Nach Fertigstellung des Gesamtfilms:** Pipeline setzt den Lüfter automatisch zurück auf **vBIOS-Automatik (leise)**.

Dies ist in [`scripts/auto_movie_maker.py`](../scripts/auto_movie_maker.py) über die Pre- und Post-Flight Hooks vorbereitet.

