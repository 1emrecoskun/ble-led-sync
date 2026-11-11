# Security & Responsible Use

This project controls **your own** Bluetooth LE LED strip (LEDBLE / Triones
family). It is a local, offline tool: no cloud, no accounts, no telemetry.

## Intended use
- Control LED strips you own.
- Research and education on BLE GATT protocols and IoT device behavior.

## Not intended
- Controlling devices you do not own or have no permission to operate.
- Any use that violates local laws or the rights of others.

## IoT security notes (why this exists)
Cheap BLE LED controllers in the LEDBLE/Triones family typically expose an
unauthenticated GATT characteristic (`0000ffe1-...`) that accepts raw RGB
commands from any client in radio range. This project demonstrates that
property. If you are a device owner, be aware that **anyone nearby can
change your strip's color** unless the controller supports pairing/bonding.

## Legal disclaimer
This software is provided "as is" without warranty. The author is not
responsible for any misuse, damage, or legal consequences resulting from
the use of this software. Use only on devices you own or have explicit
permission to test.
