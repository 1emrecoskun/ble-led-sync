import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

class AutostartTests(unittest.TestCase):
    def setUp(self):
        tk=types.ModuleType('tkinter'); tk.ttk=types.ModuleType('tkinter.ttk'); tk.messagebox=types.ModuleType('tkinter.messagebox')
        spec=importlib.util.spec_from_file_location('led_sync.app_helpers_test',Path(__file__).parents[1]/'led_sync/app.py')
        self.mod=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'tkinter':tk}): spec.loader.exec_module(self.mod)
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.desktop=self.root/'app.desktop'; self.auto=self.root/'autostart/app.desktop'
    def tearDown(self): self.temp.cleanup()
    def run_setting(self,value):
        with patch.object(self.mod,'DESKTOP',self.desktop),patch.object(self.mod,'autostart_path',return_value=self.auto):
            self.mod.set_autostart(value)
    def test_background_added(self):
        self.desktop.write_text('[Desktop Entry]\nExec="/home/test/run.sh"\nName=LED\n')
        self.run_setting(True)
        self.assertIn('Exec="/home/test/run.sh" --background',self.auto.read_text())
    def test_idempotent(self):
        self.desktop.write_text('[Desktop Entry]\nExec="/home/test/run.sh" --background\n')
        self.run_setting(True); self.run_setting(True)
        self.assertEqual(self.auto.read_text().count('--background'),1)
    def test_disable(self):
        self.auto.parent.mkdir(); self.auto.write_text('test')
        self.run_setting(False); self.assertFalse(self.auto.exists())
    def test_missing_launcher(self):
        with self.assertRaises(RuntimeError): self.run_setting(True)
    def test_manual_launcher_unchanged(self):
        text='[Desktop Entry]\nExec="/home/test/run.sh"\n'; self.desktop.write_text(text)
        self.run_setting(True); self.assertEqual(self.desktop.read_text(),text)

if __name__=='__main__': unittest.main()
