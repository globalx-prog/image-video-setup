# 🚀 AMD Radeon PRO W7800 (48 GB) Tuning- & Lüfter-Guide
> **Fokus:** Maximale Rechenleistung, Beseitigung von thermischem Downclocking und optimale Lüfterkurve unter ROCm 6.4 & Linux.

---

## 1. 🔍 Warum ist Werkseinstellung der W7800 nicht das Optimum?

Die **AMD Radeon PRO W7800** (Navi 31, RDNA3, 48 GB GDDR6 ECC) ist eine Hochleistungs-Workstation-Karte. Ab Werk ist sie jedoch sehr konservativ konfiguriert:

1. **Power-Limit auf 205 Watt gedrosselt:**  
   Das vBIOS erlaubt bis zu **230 Watt**, ab Werk sind jedoch nur 205 Watt freigegeben. Bei schweren Matrix-Multiplikationen (MiniMax H3 Diffusion) läuft die GPU durchgehend ins 205W-Limit und taktet die Rechenkerne herunter.
2. **Zu leise Blower-Lüfterkurve:**  
   Der Radiallüfter (Blower) ist auf maximale Büro-Stille ausgelegt. Selbst wenn der **Hotspot (Junction) 87 °C bis 90 °C** erreicht, dreht der Lüfter nur mit ca. **40–43 %**!
3. **Thermisches Downbinning ab 85 °C:**  
   Ab 85 °C Hotspot senkt die RDNA3-Architektur dynamisch die Boost-Spannung und Taktraten um 80–150 MHz, um nicht über 95 °C zu steigen.
4. **Takt-Latenz durch `auto`-DPM:**  
   Zwischen den einzelnen Diffusions-Schritten oder VAE-Aufrufen taktet der Treiber die GPU für Sekundenbruchteile auf 500 MHz herunter. Das ständige Hoch- und Runterspringen kostet spürbare Latenz.

---

## 2. ⚡ Die 4 Tuning-Hebel im Überblick

| Hebel | Werkseinstellung | Optimierter Wert | Was bringt das? |
| :--- | :---: | :---: | :--- |
| **1. Power-Limit** | `205 Watt` | **`230 Watt` (+12.2 %)** | Erlaubt den Rechenkernen, unter Volllast von ~1800 MHz auf **2050–2150 MHz** hochzutakten, ohne ins Power-Limit zu laufen. |
| **2. Power-Profil** | `0 BOOTUP_DEFAULT` | **`5 COMPUTE`** | Setzt `MinActiveFreq` auf mindestens 1000 MHz; optimiert die Phasenschleife für GPGPU/Tensor-Workloads. |
| **3. DPM-Level** | `auto` | **`high`** | Fixiert den VRAM-Takt permanent auf **1124 MHz** (volle ~864 GB/s Speicherbandbreite ohne Takt-Dips). |
| **4. Lüftersteuerung** | `Automatik (~42 %)` | **`65 % Manuell` oder Dynamisch** | Senkt Hotspot von 88 °C auf **68–72 °C**! Beseitigt thermisches Drosseln komplett. |

> [!TIP]
> **Performance-Zuwachs in der Praxis:**  
> Bei 12 Szenen MiniMax H3 (8 Steps) sinkt die reine Diffusionszeit von ca. 70s pro Clip auf **ca. 58–62s pro Clip** (~12–15 % schnellerer Workflow), während die Karte kühler bleibt!

---

## 3. 🛠️ Das fertige All-in-One Skript: `w7800_perf_boost.sh`

Wir haben im Projektordner das Werkzeug [`scripts/w7800_perf_boost.sh`](../scripts/w7800_perf_boost.sh) bereitgestellt.

### A. Status überprüfen (ohne Root):
```bash
./scripts/w7800_perf_boost.sh status
```
Zeigt sofort das aktuelle Power-Limit, die Temperaturen (Edge/Hotspot), das DPM-Level und die Lüfterdrehzahl an.

### B. Maximalen Performance-Boost aktivieren (mit sudo):
```bash
sudo ./scripts/w7800_perf_boost.sh boost
```
* Setzt Power-Limit auf **230 Watt**
* Aktiviert Profil **`5 COMPUTE`**
* Arretiert DPM auf **`high`**
* Setzt den Blower-Lüfter auf **65 %** (hörbar, aber hält die GPU unter 72 °C)

### C. Dynamische Lüfterkurve laufen lassen (temperaturgeführt):
```bash
sudo ./scripts/w7800_perf_boost.sh fan-curve
```
Passt den Lüfter alle 2 Sekunden stufenlos an die Hotspot-Temperatur an:
* **< 55 °C Hotspot:** 37 % PWM (nahezu unhörbar für Desktop/Office)
* **55–65 °C Hotspot:** 53 % PWM
* **65–75 °C Hotspot:** 65 % PWM (Sweet Spot beim Rendern)
* **75–83 °C Hotspot:** 76 % PWM
* **> 83 °C Hotspot:** 88 % PWM (Notfall-Kühlung)
* Beim Beenden mit `Ctrl+C` wird die Lüftersteuerung automatisch wieder an das vBIOS übergeben!

### D. Zurück auf Werkszustand:
```bash
sudo ./scripts/w7800_perf_boost.sh reset
```

---

## 4. 🧠 Software-Tuning: PyTorch & ROCm 6.4 Umgebungsvariablen

Neben der Hardware-Ebene beschleunigen folgende Umgebungsvariablen ROCm 6.4 auf der gfx1100-Architektur:

```bash
# 1. Bevorzuge hipBLASLt für extrem schnelle Matrix-Multiplikation (FP16/BF16)
export TORCH_BLAS_PREFER_HIPBLASLT=1

# 2. Deaktiviere Kernel-Serialisierung
export AMD_SERIALIZE_KERNEL=0

# 3. Erzwinge native RDNA3-Befehlspfade
export HSA_OVERRIDE_GFX_VERSION=11.0.0
```

Diese Variablen können in die `~/.bashrc` oder in die ComfyUI-Startskripte (`start_comfyui.sh` / `run_1min_movie.sh`) eingetragen werden.

---

## 5. ⚙️ Optional: Dauerhafte Aktivierung beim Systemstart (systemd)

Wenn Sie möchten, dass die W7800 bei jedem Booten automatisch mit 230 Watt und Compute-Profil startet:

Erstellen Sie eine Service-Datei `/etc/systemd/system/w7800-boost.service`:

```ini
[Unit]
Description=AMD Radeon PRO W7800 Performance Boost
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
sudo systemctl enable w7800-boost.service
```

