# Contributing

Thanks for your interest! This project is small and welcomes focused PRs.

## Dev setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install bleak mss numpy
python -m unittest discover -s tests -v
```

## Guidelines
- Keep changes small and focused. One concern per PR.
- Add/adjust unit tests for any logic change (see `tests/`).
- Do not commit logs, state files, device addresses, or personal data.
- Follow existing style (PEP 8-ish, no heavy frameworks).
- Test on Linux Mint/Ubuntu with an X11 session if touching screen capture.

## Reporting bugs
Use the issue templates. Include OS, session type (X11/Wayland), Python version,
and a sanitized log excerpt from `~/.local/state/ble-led-sync/uygulama.log`.

## Code of conduct
By participating you agree to follow `CODE_OF_CONDUCT.md`. Be kind, keep
discussions technical, and never post other people's MAC addresses, locations,
or captured audio/screen content.

## Security
See `SECURITY.md`. Report vulnerabilities privately if possible. Never open a
public issue containing a live Bluetooth address, token, or personal path.
