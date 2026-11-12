# Troubleshooting

## "Device not found"

The strip accepts one Bluetooth connection at a time. Check, in this order:

1. The strip is powered and in range.
2. The phone app (LED LAMP, HappyLighting, …) is **closed**, not just in the
   background.
3. Bluetooth is on: `rfkill list bluetooth` must not say `Soft blocked: yes`,
   and `bluetoothctl show` must say `Powered: yes`.
4. The device name in `⋯ → Settings` matches what the strip advertises
   (`LEDBLE-…` by default); the field is there for renamed strips.

The application retries on its own every few seconds.

## Screen mode does nothing

Screen capture needs an X11 display. On Wayland the application refuses to
start screen mode instead of silently falling back to a stale frame; use audio
mode, or log in with "Xorg" on the login screen.

## There is no tray icon

A tray needs a StatusNotifierItem host. On GNOME that means the *AppIndicator
and KStatusNotifierItem Support* extension; KDE and most bars have it built in.
Without a host the application simply keeps running in the background.

## I started it and see nothing

That is the intended behaviour: at login and with `--background` it starts
hidden, scans and runs the LED without a window. Open **BLE LED Sync** from the
application menu to get the window; opening it again raises the running copy
instead of starting a second one.

## How do I stop it completely?

Open the window, then `⋯ → Quit completely`. Closing the window only hides it.

## Where are the logs?

`~/.local/state/ble-led-sync/logs/uygulama.log` (rotated, two old copies kept).
`run.sh` also writes the launcher output to
`~/.local/state/ble-led-sync/baslatma.log`.

## What is in the diagnostics report?

`⋯ → Diagnostics` writes a text file under
`~/.local/state/ble-led-sync/`. Bluetooth addresses are masked before you paste
it anywhere, but file paths and operating-system details remain; read it before
sharing.

## Autostart

`⋯` in the window, or the checkbox: it writes
`~/.config/autostart/ble-led-sync.desktop`. The installer enables it
(hidden start) on a fresh install; turn the checkbox off if you would rather
start the application yourself.
