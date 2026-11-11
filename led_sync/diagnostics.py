"""Read-only environment diagnostics. No audio/screen capture or BLE writes."""
import datetime
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from .core import session_type

MAC_RE = re.compile(r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b')

if platform.system() == 'Windows':
    STATE = Path(os.environ.get('APPDATA', str(Path.home()/'AppData'/'Roaming'))) / 'ble-led-sync'
elif platform.system() == 'Darwin':
    STATE = Path.home() / 'Library' / 'Application Support' / 'ble-led-sync'
else:
    STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local'/'state'))) / 'ble-led-sync'

def cmd(args, timeout=5):
    if not shutil.which(args[0]):
        return f'NOT FOUND: {args[0]}'
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, 'LC_ALL':'C'})
        return f'Exit={p.returncode}\n{p.stdout}{p.stderr}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

def redact(text):
    """Hide Bluetooth MAC addresses; reports are often pasted into public issues."""
    return MAC_RE.sub('XX:XX:XX:XX:XX:XX', text)

def collect():
    parts = ['BLE LED Sync 0.2.0 — local diagnostics',
             datetime.datetime.now().isoformat(timespec='seconds'),
             f'Python: {platform.python_version()} | kernel: {platform.release()}',
             f'Session: {session_type(os.environ)}',
             'This report is not a test result. Bluetooth addresses are masked, '
             'but file paths and device names may still be present.']
    for path in ('/etc/os-release', '/etc/linuxmint/info'):
        try: parts.append(f'\n{path}\n{Path(path).read_text()}')
        except OSError: pass
    checks = [
        ['free','-h'], ['df','-h',str(Path.home())],
        ['bluetoothctl','list'], ['bluetoothctl','show'], ['rfkill','list','bluetooth'],
        ['systemctl','is-active','bluetooth'],
        ['systemctl','--user','is-active','pipewire','pipewire-pulse','pulseaudio'],
        ['pactl','info'], ['pactl','get-default-sink'],
        ['pactl','list','short','sinks'], ['pactl','list','short','sources'],
        ['wpctl','status'], ['aplay','-l'],
        ['systemctl','--user','is-active','xdg-desktop-portal'],
    ]
    for args in checks:
        parts.append('\n$ ' + ' '.join(args) + '\n' + cmd(args))
    s = session_type(os.environ)
    parts.append('\nSCREEN PATH: ' + (
        'X11 → MSS candidate. Real capture tested when SCREEN starts.' if s == 'x11' else
        'Wayland → this version does not capture the screen. Portal/PipeWire integration not yet available; no silent XWayland fallback.' if s == 'wayland' else
        'Session undetermined; screen mode will be blocked.'))
    parts.append('\nAUDIO PATH: output monitor source via pactl/parec; microphone not used.\n'
                 'PipeWire-Pulse or PulseAudio required; ALSA-only not supported.\n'
                 'Audio capture is Linux-only in this version.\n'
                 'BLE: diagnostics did not scan/connect/write; test separately with RED TEST in the UI.')
    return redact('\n'.join(parts))

def save():
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / ('diagnostics-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.txt')
    path.write_text(collect(), encoding='utf-8')
    return path

if __name__ == '__main__':
    print(save())
