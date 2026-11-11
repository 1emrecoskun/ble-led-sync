# Contributing

Thanks for your interest! This project is small and welcomes focused PRs.

## Dev setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .                 # pulls in bleak, mss, numpy, desktop-lifecycle
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
and a sanitized log excerpt from
`~/.local/state/ble-led-sync/logs/uygulama.log`.

## Sign-off (Developer Certificate of Origin)

Every commit must carry a `Signed-off-by` line:

```bash
git commit -s -m "Fix autostart toggle on Wayland"
```

That line certifies the [Developer Certificate of Origin 1.1](https://developercertificate.org/):
you wrote the change, or you have the right to submit it under this project's
MIT licence.

## Code of conduct
By participating you agree to follow `CODE_OF_CONDUCT.md`. Be kind, keep
discussions technical, and never post other people's MAC addresses, locations,
or captured audio/screen content.

## Security
See `SECURITY.md`. Report vulnerabilities privately if possible. Never open a
public issue containing a live Bluetooth address, token, or personal path.
