#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/ble-led-sync"
mkdir -p "$STATE"
if [[ ! -x "$HERE/.venv/bin/python" ]]; then
  if command -v zenity >/dev/null; then zenity --error --text='Önce indirilen paketteki KUR.sh dosyasını çalıştırın.'; fi
  exit 1
fi
export PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}"
cd "$HERE"
if ! "$HERE/.venv/bin/python" -m led_sync.app "$@" >>"$STATE/baslatma.log" 2>&1; then
  if command -v zenity >/dev/null; then zenity --error --text="Uygulama açılamadı. Ayrıntı: $STATE/baslatma.log"; fi
  exit 1
fi
