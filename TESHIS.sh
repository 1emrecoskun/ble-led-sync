#!/usr/bin/env bash
# Kurulumsuz hafif teşhis; yönetici yetkisi istemez, ayar değiştirmez.
set -u
OUT="$HOME/ble-led-teshis-$(date +%Y%m%d-%H%M%S).txt"
{
 echo 'BLE LED SYNC — kurulum öncesi teşhis'
 date -Iseconds
 cat /etc/os-release
 printf '\nOturum: %s | DISPLAY var: %s | WAYLAND_DISPLAY var: %s\n' "${XDG_SESSION_TYPE:-bilinmiyor}" "${DISPLAY:+evet}" "${WAYLAND_DISPLAY:+evet}"
 for c in 'free -h' 'df -h .' 'bluetoothctl list' 'bluetoothctl show' 'rfkill list bluetooth' 'pactl info' 'pactl list short sinks' 'pactl list short sources' 'wpctl status' 'aplay -l'; do
   printf '\n--- %s ---\n' "$c"
   timeout 6s bash -c "$c" 2>&1 || true
 done
 echo 'Bu rapor BLE bağlantı/yazma veya ses/ekran yakalama testi değildir.'
} > "$OUT" 2>&1
printf 'Rapor: %s\n' "$OUT"
if command -v xdg-open >/dev/null; then xdg-open "$OUT" >/dev/null 2>&1 || true; fi
