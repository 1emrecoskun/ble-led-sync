#!/usr/bin/env bash
# Installer for Linux Mint / Ubuntu (Debian family). Runs per-user; never as root.
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

case "${LC_ALL:-}${LC_MESSAGES:-}${LANG:-}" in
  *[Tt][Rr]*) LANG_IS_TR=1 ;;
  *) LANG_IS_TR=0 ;;
esac
say() {
  if [[ "$LANG_IS_TR" == 1 ]]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi
}
prompt() {
  if [[ "$LANG_IS_TR" == 1 ]]; then read -r -p "$2" REPLY || true
  else read -r -p "$1" REPLY || true; fi
}

if [[ ! -t 0 && "${1:-}" != '--terminal' ]]; then
  if command -v gnome-terminal >/dev/null; then exec gnome-terminal --wait -- bash "$HERE/KUR.sh" --terminal
  elif command -v x-terminal-emulator >/dev/null; then exec x-terminal-emulator -e bash "$HERE/KUR.sh" --terminal
  else
    say 'Open a terminal in this folder and run: bash KUR.sh' 'Klasörde terminal açıp bash KUR.sh çalıştırın.'
    exit 1
  fi
fi

STATE="${XDG_STATE_HOME:-$HOME/.local/state}/ble-led-sync"
mkdir -p "$STATE"
LOG="$STATE/install-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
trap 'code=$?; if [[ $code -ne 0 ]]; then say "Installation failed. Log: $LOG" "Kurulum başarısız. Log: $LOG"; prompt "Press Enter to close…" "Kapatmak için Enter…"; fi; exit $code' ERR

if [[ "$EUID" -eq 0 ]]; then
  say 'Run this script as your normal user, not with sudo.' 'Bu betiği sudo ile değil normal kullanıcıyla çalıştırın.'
  exit 1
fi
if ! command -v apt-get >/dev/null; then
  say 'This installer targets Linux Mint / Ubuntu (apt).' 'Bu kurucu Linux Mint / Ubuntu ailesi içindir.'
  exit 1
fi

if ! /usr/bin/python3 - "$STATE/instance.lock" <<'PYLOCK'
import fcntl,sys
with open(sys.argv[1],'a') as f:
    try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: sys.exit(1)
PYLOCK
then
  say 'Close the running BLE LED Sync app completely, then run the installer again.' \
      'Önce çalışan BLE LED Sync uygulamasını tamamen kapatın; sonra kurulumu tekrar çalıştırın.'
  prompt "Press Enter to close…" "Kapatmak için Enter…"
  exit 1
fi

VERSION="$(sed -n "s/^__version__[[:space:]]*=[[:space:]]*'\([^']*\)'.*/\1/p" "$HERE/led_sync/__init__.py" 2>/dev/null | head -n1)"
VERSION="${VERSION:-0.2.0}"

printf '\nBLE LED SYNC %s — experimental Linux build\n' "$VERSION"
say 'The installer downloads system packages from apt and Python packages from PyPI.' \
    'Kurucu apt depolarından sistem paketlerini, PyPI üzerinden Python paketlerini indirir.'
say 'No paid API is used. Audio mode starts automatically after install; use the tray icon to stop or quit.' \
    'Ücretli API yok. Kurulum sonrasında SES otomatik başlar; tepsi simgesinden durdurabilir veya çıkabilirsiniz.'
say 'Packages: python3-venv python3-tk pulseaudio-utils bluez alsa-utils python3-gi gir1.2-gtk-3.0 (+ indicator)' \
    'Paketler: python3-venv python3-tk pulseaudio-utils bluez alsa-utils python3-gi gir1.2-gtk-3.0 (+ gösterge)'
say 'If a package manager update is running, wait for it to finish first.' \
    'Açık Güncelleme Yöneticisi işlemi varsa önce tamamlanmasını bekleyin.'
prompt 'Continue with the installation? [y/N]: ' 'Kuruluma devam edilsin mi? [e/H]: '
case "$REPLY" in [yYeE]*) ;; *) say 'Cancelled.' 'İptal edildi.'; exit 0;; esac

sudo apt-get update
sudo apt-get install -y python3-venv python3-tk pulseaudio-utils bluez alsa-utils python3-gi gir1.2-gtk-3.0
sudo apt-get install -y gir1.2-ayatanaappindicator3-0.1 \
  || sudo apt-get install -y gir1.2-appindicator3-0.1 \
  || say 'No tray indicator package found; the app runs without a tray icon.' \
         'Tepsi simgesi paketi bulunamadı; uygulama tepsisiz çalışır.'

TARGET="$HOME/.local/share/ble-led-sync"
mkdir -p "$TARGET"
if [[ -d "$TARGET/led_sync" && "$HERE" != "$TARGET" ]]; then
  BACKUP="$HOME/.local/share/ble-led-sync-backups/$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BACKUP"
  cp -a "$TARGET/led_sync" "$BACKUP/"
  for f in run.sh requirements.txt; do [[ ! -f "$TARGET/$f" ]] || cp -a "$TARGET/$f" "$BACKUP/"; done
  say "Previous application code backed up to: $BACKUP" "Önceki uygulama kodu yedeklendi: $BACKUP"
fi
if [[ "$HERE" != "$TARGET" ]]; then
  for item in led_sync requirements.txt run.sh README.md README.tr.md LICENSE icon.svg; do
    if [[ -e "$HERE/$item" ]]; then cp -a "$HERE/$item" "$TARGET/"
    else say "note: $item missing, skipped" "not: $item bulunamadı, atlandı"; fi
  done
fi

/usr/bin/python3 -m venv --system-site-packages "$TARGET/.venv"
"$TARGET/.venv/bin/python" -m pip install --disable-pip-version-check -r "$TARGET/requirements.txt"
"$TARGET/.venv/bin/python" - <<'PYDEPS'
import sys
missing = []
try:
    import tkinter
except ImportError:
    missing.append('python3-tk')
for module in ('bleak', 'mss', 'numpy'):
    try:
        __import__(module)
    except ImportError:
        missing.append(module)
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk  # noqa: F401
except Exception:
    missing.append('python3-gi + gir1.2-gtk-3.0')
indicator = False
for namespace in ('AyatanaAppIndicator3', 'AppIndicator3'):
    try:
        import gi
        gi.require_version(namespace, '0.1')
        __import__('gi.repository', fromlist=[namespace])
        indicator = True
        break
    except Exception:
        continue
if not indicator:
    print('WARNING: no AppIndicator library; the window will stay open instead of using a tray icon.')
if missing:
    print('MISSING: ' + ', '.join(missing))
    sys.exit(1)
print('Python dependencies imported.')
PYDEPS
chmod +x "$TARGET/run.sh"

LANG_IS_TR="$LANG_IS_TR" TARGET="$TARGET" "$TARGET/.venv/bin/python" - <<'PY'
import os
import pathlib
import shutil
import subprocess

from desktop_lifecycle import App, install_icon, install_menu_entry

target = pathlib.Path(os.environ['TARGET'])
turkish = os.environ.get('LANG_IS_TR') == '1'
run = str(target / 'run.sh')

app = App('ble-led-sync').ensure_dirs()
icon = install_icon(app.paths, target / 'icon.svg', 'ble-led-sync')
entry = install_menu_entry(
    app.paths, 'ble-led-sync', [run],
    display_name='BLE LED Sync',
    comment='Yerel ses ve ekran senkronizasyonu' if turkish else 'Local audio and screen sync',
    icon=icon,
    categories=('AudioVideo', 'Utility'),
    extra={'StartupWMClass': 'Ble-led-sync'},
)
app.autostart([run], display_name='BLE LED Sync',
              comment='BLE LED Sync arka planda başlasın' if turkish
              else 'Start BLE LED Sync in the background at login').enable()

if shutil.which('xdg-user-dir'):
    out = subprocess.run(['xdg-user-dir', 'DESKTOP'], capture_output=True, text=True)
    folder = pathlib.Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None
    if folder and folder != pathlib.Path.home() and folder.is_dir():
        dst = folder / entry.name
        shutil.copyfile(entry, dst)
        dst.chmod(0o755)
        if shutil.which('gio'):
            subprocess.run(['gio', 'set', str(dst), 'metadata::trusted', 'true'], capture_output=True)
print(('Menu launcher written: ' if not turkish else 'Menü başlatıcısı oluşturuldu: ') + str(entry))
PY

say 'INSTALLATION FINISHED. This does not prove the real LED/audio/screen test passed.' \
    'KURULUM TAMAMLANDI. Bu, gerçek LED/ses/ekran testinin geçtiği anlamına gelmez.'
say 'Search for "BLE LED Sync" in the Mint menu. Close the phone LED LAMP app. Audio mode starts automatically.' \
    'Mint menüsünde BLE LED Sync arayın. Telefonun LED LAMP uygulamasını kapatın. SES otomatik başlar.'
say "Install log: $LOG" "Kurulum logu: $LOG"
prompt "Press Enter to close…" "Kapatmak için Enter…"
