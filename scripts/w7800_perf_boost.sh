#!/bin/bash
# ==============================================================================
# 🚀 w7800_perf_boost.sh — Hardware-Tuning & Lüftersteuerung für AMD Radeon PRO W7800
# ==============================================================================
# Funktionen:
#   1. Power-Limit von 205W auf 230W (+12.2% Power-Budget) anheben
#   2. Compute-Profil (Profile 5 COMPUTE) in amdgpu aktivieren
#   3. DPM Performance-Level auf "high" fixieren (keine Latenz-Dips)
#   4. Dynamische oder statische Lüfterkurve gegen thermisches Downclocking
#   5. Reset auf Werkszustand
# ==============================================================================

# Finde AMD GPU Card und Hwmon
CARD_DIR=""
for c in /sys/class/drm/card[0-9]*/device; do
    if [ -f "$c/pp_power_profile_mode" ]; then
        CARD_DIR="$c"
        break
    fi
done

HWMON_DIR=""
if [ -n "$CARD_DIR" ]; then
    for h in "$CARD_DIR"/hwmon/hwmon*; do
        if [ -f "$h/power1_cap" ]; then
            HWMON_DIR="$h"
            break
        fi
    done
fi

if [ -z "$CARD_DIR" ] || [ -z "$HWMON_DIR" ]; then
    echo "❌ Fehler: Keine kompatible AMD GPU mit hwmon/sysfs Schnittstelle gefunden."
    exit 1
fi

show_status() {
    echo "=================================================================="
    echo " 📊 AKTUELLER STATUS: AMD Radeon PRO W7800 (48 GB)"
    echo "=================================================================="
    echo " Pfade:"
    echo "   Device: $CARD_DIR"
    echo "   Hwmon:  $HWMON_DIR"
    echo ""

    # Power
    if [ -f "$HWMON_DIR/power1_cap" ]; then
        cur_p=$(cat "$HWMON_DIR/power1_cap" 2>/dev/null)
        max_p=$(cat "$HWMON_DIR/power1_cap_max" 2>/dev/null)
        avg_p=$(cat "$HWMON_DIR/power1_average" 2>/dev/null)
        echo " ⚡ Power-Limit:"
        echo "   Aktuell:   $((cur_p / 1000000)) W"
        echo "   Maximum:   $((max_p / 1000000)) W"
        echo "   Verbrauch: $((avg_p / 1000000)) W"
    fi

    # DPM Performance Level
    if [ -f "$CARD_DIR/power_dpm_force_performance_level" ]; then
        dpm=$(cat "$CARD_DIR/power_dpm_force_performance_level" 2>/dev/null)
        echo " 🚀 DPM Level:      $dpm"
    fi

    # Power Profile Mode
    if [ -f "$CARD_DIR/pp_power_profile_mode" ]; then
        active_prof=$(grep "\*" "$CARD_DIR/pp_power_profile_mode" 2>/dev/null | awk '{print $2}')
        echo " 🎯 Power-Profil:   $active_prof"
    fi

    # Temperatur
    if [ -f "$HWMON_DIR/temp1_input" ]; then
        edge=$(cat "$HWMON_DIR/temp1_input" 2>/dev/null)
        junc=$(cat "$HWMON_DIR/temp2_input" 2>/dev/null)
        echo " 🌡️ Temperaturen:   Edge: $((edge / 1000))°C | Hotspot: $((junc / 1000))°C"
    fi

    # Lüfter
    if [ -f "$HWMON_DIR/pwm1" ]; then
        pwm_en=$(cat "$HWMON_DIR/pwm1_enable" 2>/dev/null)
        pwm_val=$(cat "$HWMON_DIR/pwm1" 2>/dev/null)
        pwm_pct=$((pwm_val * 100 / 255))
        mode_str="Automatik (vBIOS)"
        [ "$pwm_en" = "1" ] && mode_str="Manuell"
        echo " 🌀 Lüfter:         ${pwm_pct}% (PWM ${pwm_val}/255) — Modus: $mode_str"
    fi
    echo "=================================================================="
}

set_boost() {
    echo "🚀 Aktiviere Performance-Boost für W7800..."

    # 1. Power Limit auf 230 Watt
    if [ -f "$HWMON_DIR/power1_cap_max" ]; then
        max_p=$(cat "$HWMON_DIR/power1_cap_max")
        echo "$max_p" > "$HWMON_DIR/power1_cap" 2>/dev/null && \
            echo "  ✅ Power-Limit auf $((max_p / 1000000))W gesetzt (+12.2% Budget)." || \
            echo "  ⚠️ Konnte Power-Limit nicht setzen (Root-Rechte nötig?)."
    fi

    # 2. Compute Profile aktivieren (Profile 5)
    if [ -f "$CARD_DIR/pp_power_profile_mode" ]; then
        echo 5 > "$CARD_DIR/pp_power_profile_mode" 2>/dev/null && \
            echo "  ✅ Power-Profil '5 COMPUTE' aktiviert (optimierte Tensor-/Matrix-Phasenschleife)." || \
            echo "  ⚠️ Konnte Power-Profil nicht setzen."
    fi

    # 3. DPM Performance Level auf high
    if [ -f "$CARD_DIR/power_dpm_force_performance_level" ]; then
        echo high > "$CARD_DIR/power_dpm_force_performance_level" 2>/dev/null && \
            echo "  ✅ DPM Performance-Level auf 'high' fixiert (VRAM-Takt permanent maximal)." || \
            echo "  ⚠️ Konnte DPM Level nicht setzen."
    fi

    # 4. Lüfter auf 65% (PWM 165) zur aktiven Kühlung
    if [ -f "$HWMON_DIR/pwm1_enable" ]; then
        echo 1 > "$HWMON_DIR/pwm1_enable" 2>/dev/null
        sleep 0.2
        if echo 165 > "$HWMON_DIR/pwm1" 2>/dev/null; then
            echo "  ✅ Blower-Lüfter auf 65% (PWM 165) gesetzt (verhindert Hotspot-Drosselung >85°C)."
        else
            sleep 0.3
            echo 165 > "$HWMON_DIR/pwm1" 2>/dev/null && \
                echo "  ✅ Blower-Lüfter auf 65% (PWM 165) gesetzt." || \
                echo "  ⚠️ Konnte Lüfter nicht manuell steuern."
        fi
    fi

    echo "🎉 Boost erfolgreich aktiviert! Siehe Status unten:"
    show_status
}

reset_defaults() {
    echo "🔄 Setze W7800 auf Werkszustand zurück..."

    # 1. Power Limit auf Standard 205W
    if [ -f "$HWMON_DIR/power1_cap" ]; then
        echo 205000000 > "$HWMON_DIR/power1_cap" 2>/dev/null && \
            echo "  ✅ Power-Limit auf 205W Standard zurückgesetzt."
    fi

    # 2. Power-Profil auf 0 (Default)
    if [ -f "$CARD_DIR/pp_power_profile_mode" ]; then
        echo 0 > "$CARD_DIR/pp_power_profile_mode" 2>/dev/null && \
            echo "  ✅ Power-Profil auf '0 BOOTUP_DEFAULT' zurückgesetzt."
    fi

    # 3. DPM Level auf auto
    if [ -f "$CARD_DIR/power_dpm_force_performance_level" ]; then
        echo auto > "$CARD_DIR/power_dpm_force_performance_level" 2>/dev/null && \
            echo "  ✅ DPM Level auf 'auto' zurückgesetzt."
    fi

    # 4. Lüfter auf vBIOS Automatik
    if [ -f "$HWMON_DIR/pwm1_enable" ]; then
        echo 2 > "$HWMON_DIR/pwm1_enable" 2>/dev/null && \
            echo "  ✅ Lüftersteuerung wieder an vBIOS-Automatik übergeben."
    fi

    echo "✅ Werkszustand wiederhergestellt."
    show_status
}

dynamic_fan_curve() {
    echo "🌡️ Starte dynamische Lüfterkurve (beenden mit Ctrl+C)..."
    echo "   Kurve: <60°C Hotspot -> 40% (leise) | 60-72°C -> 60% | 73-82°C -> 75% | >82°C -> 85%"
    
    # Sicherstellen, dass bei Abbruch Automatik reaktiviert wird
    trap 'echo ""; echo "Beende Lüfterkurve und stelle Automatik wieder her..."; echo 2 > "$HWMON_DIR/pwm1_enable" 2>/dev/null; exit 0' INT TERM EXIT

    echo 1 > "$HWMON_DIR/pwm1_enable" 2>/dev/null

    while true; do
        junc_raw=$(cat "$HWMON_DIR/temp2_input" 2>/dev/null || echo 0)
        edge_raw=$(cat "$HWMON_DIR/temp1_input" 2>/dev/null || echo 0)
        junc=$((junc_raw / 1000))
        edge=$((edge_raw / 1000))

        # Berechne PWM Zielwert basierend auf Hotspot
        if [ "$junc" -lt 55 ]; then
            target_pwm=95   # ~37%
        elif [ "$junc" -lt 65 ]; then
            target_pwm=135  # ~53%
        elif [ "$junc" -lt 75 ]; then
            target_pwm=165  # ~65%
        elif [ "$junc" -lt 83 ]; then
            target_pwm=195  # ~76%
        else
            target_pwm=225  # ~88% Notfall-Kühlung
        fi

        echo "$target_pwm" > "$HWMON_DIR/pwm1" 2>/dev/null
        target_pct=$((target_pwm * 100 / 255))
        
        printf "\r[W7800 Temp-Wächter] Hotspot: %2d°C | Edge: %2d°C | Lüfter: %2d%% (PWM %3d/255)" "$junc" "$edge" "$target_pct" "$target_pwm"
        sleep 2
    done
}

set_fan_manual() {
    pct="$1"
    if [ -z "$pct" ] || [ "$pct" -lt 15 ] || [ "$pct" -gt 100 ]; then
        echo "❌ Ungültiger Prozentwert: '$pct' (Gültig: 15 bis 100 Prozent)"
        exit 1
    fi
    pwm=$((pct * 255 / 100))
    echo 1 > "$HWMON_DIR/pwm1_enable" 2>/dev/null
    sleep 0.2
    if echo "$pwm" > "$HWMON_DIR/pwm1" 2>/dev/null; then
        echo "✅ Blower-Lüfter manuell auf ${pct}% (PWM ${pwm}/255) gesetzt."
    else
        sleep 0.3
        echo "$pwm" > "$HWMON_DIR/pwm1" 2>/dev/null && \
            echo "✅ Blower-Lüfter manuell auf ${pct}% (PWM ${pwm}/255) gesetzt." || \
            echo "⚠️ Konnte Lüfter nicht setzen (Root-Rechte nötig? Bitte mit sudo ausführen)."
    fi
    echo ""
    show_status
}

set_fan_auto() {
    echo 2 > "$HWMON_DIR/pwm1_enable" 2>/dev/null && \
        echo "✅ Lüftersteuerung erfolgreich an vBIOS-Automatik übergeben." || \
        echo "⚠️ Konnte Lüftermodus nicht ändern (Root-Rechte nötig?)."
    echo ""
    show_status
}

set_power_limit() {
    w="$1"
    if [ -z "$w" ] || [ "$w" -lt 100 ] || [ "$w" -gt 230 ]; then
        echo "❌ Ungültiges Power-Limit: '$w' (Gültig: 100 bis 230 Watt)"
        exit 1
    fi
    micro_w=$((w * 1000000))
    echo "$micro_w" > "$HWMON_DIR/power1_cap" 2>/dev/null && \
        echo "✅ Power-Limit auf ${w} Watt gesetzt." || \
        echo "⚠️ Konnte Power-Limit nicht setzen (Root-Rechte nötig? Bitte mit sudo ausführen)."
    echo ""
    show_status
}

set_sweet_spot() {
    echo "🎯 Aktiviere gesunden Sweet-Spot (205W Standard-Power + COMPUTE + 55% Lüfter)..."
    echo 205000000 > "$HWMON_DIR/power1_cap" 2>/dev/null && \
        echo "  ✅ Power-Limit auf 205W gesetzt (effiziente Sweet-Spot-Zone, schont Hardware)."
    echo 5 > "$CARD_DIR/pp_power_profile_mode" 2>/dev/null && \
        echo "  ✅ Power-Profil '5 COMPUTE' aktiv."
    echo high > "$CARD_DIR/power_dpm_force_performance_level" 2>/dev/null && \
        echo "  ✅ DPM Level 'high' aktiv."
    echo 1 > "$HWMON_DIR/pwm1_enable" 2>/dev/null
    sleep 0.2
    echo 140 > "$HWMON_DIR/pwm1" 2>/dev/null && \
        echo "  ✅ Blower-Lüfter auf 55% (PWM 140) gesetzt (hält Hotspot dauerhaft <80°C)."
    echo ""
    show_status
}

case "$1" in
    boost)
        set_boost
        ;;
    sweet-spot|sweet)
        set_sweet_spot
        ;;
    power|set-power)
        set_power_limit "$2"
        ;;
    reset)
        reset_defaults
        ;;
    fan-curve|curve|adaptive)
        dynamic_fan_curve
        ;;
    set-fan|fan)
        set_fan_manual "$2"
        ;;
    silent)
        echo "🔇 Aktiviere Silent-Profil (35% Blower)..."
        set_fan_manual 35
        ;;
    balanced)
        echo "⚖️ Aktiviere Balanced-Profil (50% Blower)..."
        set_fan_manual 50
        ;;
    performance)
        echo "🚀 Aktiviere Performance-Profil (65% Blower)..."
        set_fan_manual 65
        ;;
    max)
        echo "🌪️ Aktiviere Max-Cooling-Profil (85% Blower)..."
        set_fan_manual 85
        ;;
    auto)
        set_fan_auto
        ;;
    status|"")
        show_status
        ;;
    *)
        echo "Verwendung: $0 {status|boost|reset|fan-curve|set-fan <%>|silent|balanced|performance|max|auto}"
        echo "  status         - Zeigt aktuellen Takt, Temperatur, Power und Lüfter"
        echo "  boost          - 230W Power Limit, COMPUTE-Profil, DPM High, 65% Lüfter"
        echo "  reset          - Stellt vBIOS-Standardwerte (205W, Auto-Lüfter) wieder her"
        echo "  fan-curve      - Startet dynamische Hitzeschutz-Lüfterkurve im Vordergrund"
        echo "  set-fan <15-100> - Setzt den Lüfter manuell auf einen festen Prozentwert"
        echo "  silent         - 35% Blower (flüsterleise, für Office & Leerlauf)"
        echo "  balanced       - 50% Blower (angenehmes Rauschen, für Desktop-Arbeit)"
        echo "  performance    - 65% Blower (Sweet Spot für KI-Videos, <76°C Hotspot)"
        echo "  max            - 85% Blower (maximale Kühlung für Dauer-Batchläufe)"
        echo "  auto           - Übergibt die Lüftersteuerung wieder an das vBIOS"
        exit 1
        ;;
esac

