# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-11-12

### Changed

- The desktop plumbing — single-instance lock, XDG paths, tray menu, menu entry,
  autostart, rotating log — now comes from
  [`desktop-lifecycle`](https://github.com/1emrecoskun/desktop-lifecycle), which
  was extracted from this application. Behaviour is unchanged.
- The installer builds the launcher through that library, so `Exec=` is quoted
  by code that has tests for it.
- The window class is `ble-led-sync` with a matching `StartupWMClass`; the
  taskbar no longer shows a bare "Tk".

### Fixed

- At login the application starts hidden, scans for the strip and runs the last
  mode, instead of putting a window on screen.
- Closing the window hides it again; `⋯ → Quit completely` stops the process.
- The last mode (audio, screen, hybrid) is restored on the next start, and
  screen mode falls back to audio where capture is impossible.

## [0.2.0] - 2026-11-11

First public release: audio-reactive, screen-reactive and hybrid modes for
LEDBLE/Triones strips, a small Tk window, tray menu, red connection test,
diagnostics with masked Bluetooth addresses, and an installer for Linux
Mint/Ubuntu.

[Unreleased]: https://github.com/1emrecoskun/ble-led-sync/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/1emrecoskun/ble-led-sync/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/1emrecoskun/ble-led-sync/releases/tag/v0.2.0
