# BLE LED Sync — Audio & Screen Reactive LED Strip Controller

🌐 Language: **English** | [Türkçe](README.tr.md)

A small Linux desktop app that drives a cheap Bluetooth LE LED strip
(`LEDBLE-` / Triones family) from your PC: it follows the screen color,
reacts to system audio, or blends both. No cloud, no accounts, no paid APIs.

Built for the common unbranded BLE RGB strips sold as "LEDBLE-XXXX",
"Triones", "Magic Blue", "Happy Lighting", etc. (GATT characteristic
`0000ffe1-0000-1000-8000-00805f9b34fb`).

## Features
- **SES** mode — audio-reactive (FFT bands → RGB, beat envelope).
- **EKRAN** mode — screen color (X11 capture, center crop).
- **SES + EKRAN** (hybrid) — screen color with audio-driven brightness pulse.
- Turkish / English interface with an in-app language switch (auto-detected on first run).
- System tray (Ayatana AppIndicator), small ~440×392 window.
- Auto-start in SES mode on login (optional, toggle in UI).
- Brightness / sensitivity sliders, persisted.
- Red connection test (verify hardware without audio).
- Diagnostics report + rotating log.
- Reconnect with backoff; handles stale bluez connections.

## Protocol
```
Power on : 7E FF 04 01 FF FF FF FF EF
RGB      : 7E FF 05 03 R G B FF EF
Char UUID: 0000ffe1-0000-1000-8000-00805f9b34fb
Scan name: LEDBLE-XXXXXX  (set your strip's name in the UI: ⋯ → Audio output / screen settings)
```

## Platform support
- **Linux** (X11): full — audio + screen sync, tray icon, autostart. Wayland: audio only (screen capture needs X11).
- **Windows**: BLE control, red test and screen sync are implemented; audio capture is not (Linux-only in 0.2.0). No tray icon or autostart yet.
- **macOS**: BLE control, red test and screen sync are implemented; audio capture is not (that would need BlackHole plus a capture backend that does not exist yet). No tray icon or autostart yet.

Non-Linux support is young and lightly tested — bug reports are welcome.

## Requirements
- Linux (X11 session for screen capture; audio via a PulseAudio/PipeWire monitor source)
- Windows / macOS: Python 3.11+, Bluetooth adapter, screen capture permissions
- Python 3.11+
- System: `python3-tk` (GUI), `python3-gi` + GTK3 (tray, optional), `pulseaudio-utils` (Linux audio), `bluez` (Linux Bluetooth)
- Bluetooth adapter + a LEDBLE/Triones strip
- `desktop-lifecycle` (installed automatically; it owns the tray, the
  single-instance lock, the menu entry and autostart)

## Install (Linux Mint / Ubuntu family)
```bash
# extract the archive, then:
bash KUR.sh
```
The installer sets up a venv, installs `bleak`, `mss`, `numpy`,
`desktop-lifecycle`, the system
packages (`python3-tk`, `python3-gi`, GTK3, AppIndicator when available), a
menu entry and autostart. Missing optional pieces only produce a warning.

At login it starts **hidden**: the engine scans for the strip and runs the
last mode, with no window on screen. Opening **BLE LED Sync** from the menu
brings the window up; closing it hides it again. To stop the process, use
⋯ → Quit completely.

Any platform (development install):
```bash
python3 -m pip install .          # installs the `ble-led-sync` command
ble-led-sync                      # or: python3 -m led_sync.app
```

Run manually from a checkout:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh               # shows window
./run.sh --background  # start hidden: LED runs, no window
```

## Tests
```bash
python3 -m unittest discover -s tests -v
```
55 unit tests (protocol, color, beat envelope, engine, desktop integration).

## Security note
Cheap BLE LED controllers in this family usually accept unauthenticated
GATT writes from any client in radio range. This tool only controls devices
**you own**. See `SECURITY.md`.

## Documentation
- `docs/protocol-reversing.md` — BLE protocol, packet format, security
  observations (useful for IoT / red-team research).
- `SECURITY.md` — responsible use and IoT security notes.
- `CONTRIBUTING.md` — dev setup and guidelines.

## Disclaimer
This software is provided **"as is"**, without warranty of any kind, express or
implied. The author(s) shall not be liable for any direct, indirect, incidental,
special, exemplary, or consequential damages arising from the use of this
software. This tool is intended **only for controlling devices you own**.
Unauthorized access to or control of devices you do not own is illegal and is the
sole responsibility of the user. The author(s) bear no responsibility for
malicious or unlawful use.

## Built with

The window, the tray icon and the audio engine are this project's own work. The
unglamorous parts (single-instance lock, XDG paths, menu entry, autostart,
Wayland-aware tray detection, rotating logs) come from
[`desktop-lifecycle`](https://github.com/1emrecoskun/desktop-lifecycle), a small
dependency-free library extracted from this application.

## Privacy

- Audio is read from the monitor source of your own output device; the
  microphone is never used.
- Screen mode reads your own virtual display; nothing is stored and nothing is
  uploaded.
- There is no account, no telemetry, no analytics and no network client other
  than the local Bluetooth connection to your strip.
- The diagnostics report masks Bluetooth addresses before you paste it into an
  issue, but it still contains file paths and operating system details. Read it
  before you share it.

## Who made this
Built by [Emre Coşkun](https://github.com/1emrecoskun).

## License and names
MIT — see `LICENSE`. The licence covers the code, not the project name or icon,
and it grants no warranty. "LEDBLE" and "Triones" belong to their respective
owners; this project is not affiliated with them.
