"""The desktop integration is owned by desktop-lifecycle; this checks the wiring.

Importing the GUI module needs Tkinter, which CI does not always ship, so a
minimal stub is installed first. Nothing here opens a window or touches the
real home directory.
"""

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop_lifecycle import Autostart, Paths


def load_app_module():
    tk = types.ModuleType("tkinter")
    tk.ttk = types.ModuleType("tkinter.ttk")
    tk.messagebox = types.ModuleType("tkinter.messagebox")
    spec = importlib.util.spec_from_file_location(
        "led_sync.app_under_test", Path(__file__).parents[1] / "led_sync/app.py"
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"tkinter": tk}):
        spec.loader.exec_module(module)
    return module


class PathsTest(unittest.TestCase):
    def setUp(self):
        self.module = load_app_module()

    def test_paths_come_from_the_library(self):
        paths = Paths.for_app("ble-led-sync")
        self.assertEqual(self.module.CONFIG, paths.config / "settings.json")
        self.assertEqual(self.module.LIFECYCLE.name, "ble-led-sync")

    def test_no_hand_written_lock_or_path_helpers_left(self):
        for name in ("acquire_lock", "Tray", "SHOW_REQUEST"):
            self.assertFalse(hasattr(self.module, name), name)

    def test_tray_menu_keeps_the_separator(self):
        app = types.SimpleNamespace(
            lang=types.SimpleNamespace(get=lambda: "en"),
            start=lambda mode: None,
            show=lambda: None,
            stop=lambda: None,
            close=lambda: None,
        )
        with patch.object(self.module, "create_tray") as create:
            self.module.build_tray(app)
        items = create.call_args.kwargs["items"]
        self.assertIn(None, items)
        self.assertEqual(len([item for item in items if item is not None]), 6)
        self.assertEqual(create.call_args.args[0], "BLE LED Sync")


class AutostartWiringTest(unittest.TestCase):
    def setUp(self):
        self.module = load_app_module()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.autostart = Autostart(
            "ble-led-sync", ["/bin/true"], env={}, system="Linux", home=self.home
        )

    def test_toggle_writes_and_removes_the_entry(self):
        with patch.object(self.module, "AUTOSTART", self.autostart):
            self.module.set_autostart(True)
            self.assertTrue(self.autostart.enabled)
            self.assertEqual(self.autostart.target, self.module.autostart_path())
            self.module.set_autostart(False)
            self.assertFalse(self.autostart.enabled)


if __name__ == "__main__":
    unittest.main()
