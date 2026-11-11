# Reverse Engineering Notes: LEDBLE / Triones BLE LED Protocol

This document summarizes how the protocol used by this project was
recovered, for educational and interoperability purposes. It applies to
the common unbranded BLE RGB strips sold under names like LEDBLE, Triones,
Magic Blue, Happy Lighting, etc.

## Discovery
- Advertised name prefix: `LEDBLE-`, `Triones:`, `LEDBlue-`, `QHM-`, `Dream~`.
- Service UUID: `0000ffe0-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000ffe1-0000-1000-8000-00805f9b34fb`
  (properties usually include `write` and `write-without-response`).

Tools used: `bluetoothctl`, `bleak` (Python), Android "nRF Connect" for
GATT inspection, and packet capture of the vendor's mobile app.

## Methodology (how to reproduce)
1. Put the strip in pairing mode (power cycle or use the vendor app once).
2. Scan with `bluetoothctl scan on` (or `BleakScanner.discover`) and note the
   advertised name and address.
3. Inspect GATT with `bluetoothctl gatt.list-attributes <addr>` or nRF Connect:
   look for a writable characteristic under a `ffe0`/`ffe5` service.
4. Capture the vendor app's traffic (Android: enable Bluetooth HCI snoop log
   in Developer Options, then `adb pull /data/misc/bluetooth/logs/...`).
5. Diff captured writes against the characteristic to identify the frame
   format, field order, and checksums.
6. Replay minimal frames with `bleak` (`write_gatt_char`) until the strip
   responds; iterate.

## Packet format
All commands are 9 bytes, framed by `0x7E ... 0xEF`:

| Purpose | Bytes (hex) |
|---|---|
| Power on | `7E FF 04 01 FF FF FF FF EF` |
| Set RGB  | `7E FF 05 03 R  G  B  FF EF` |

- `R, G, B` are 0-255.
- The controller drives the whole strip as a single color (no per-LED
  addressing in this family).
- Writes can use either `write` (with response) or `write-without-response`;
  the device accepts both. This implementation picks based on the
  characteristic's advertised properties, preferring without-response when
  available for lower latency.

## Threat model
- **Attacker:** any BLE-capable device within radio range (~10-30 m).
- **Asset:** the visual state of the LED strip (and, indirectly, any
  inference about the victim's activity from lighting patterns).
- **Capability:** unauthenticated read/write to the GATT characteristic;
  no pairing, no bonding, no encryption.
- **Impact:** an attacker can turn the strip on/off, change colors, or
  flash patterns. No data exfiltration (the strip stores no user data).
  In shared spaces this is a nuisance / social-engineering vector
  (e.g., mimicking an alert state).
- **Out of scope:** RF jamming, physical access, supply-chain.

## Security observations
- **No authentication / pairing required.** Any client in radio range can
  connect and write commands. There is no PIN, no bonding, no ACL.
- **No encryption on the GATT characteristic** in most variants.
- **No rate limiting** observed; the device accepts writes as fast as the
  BLE link allows (this app caps at ~17 writes/s to avoid disconnects).
- Practical consequence: in a shared space, anyone with a BLE-capable
  device can change your strip's color. Treat these strips as
  "anyone can control" devices, not as trusted actuators.
- Mitigation options: keep the strip powered off when not in use, use a
  controller that supports bonding/pairing, or place it behind a
  gateway you control.

## Notes on reliability
- Some controllers disconnect when flooded; backoff (2→4→8→16→30 s) is
  used on failure.
- BlueZ may hold a stale connection after a crash; disconnect explicitly
  before scanning (see `engine.py`).
- Screen capture is X11-only in this version; Wayland portal support is
  not implemented.

## Responsible use
Only test on devices you own or have written permission to assess. The
techniques here are standard IoT interoperability research; applying them
to devices you do not own may violate local laws.

## References
- Bluetooth-Devices/led-ble (library supporting this family):
  https://github.com/Bluetooth-Devices/led-ble
- Home Assistant LED BLE integration:
  https://www.home-assistant.io/integrations/led_ble/
