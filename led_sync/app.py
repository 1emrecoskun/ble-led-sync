"""Small settings window + system tray for the LED strip. Per-user; root never required."""
import json
import logging
from pathlib import Path
import platform as _platform
import queue
import subprocess
import sys
import threading
import time

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError as exc:  # pragma: no cover - depends on the host system
    raise SystemExit(
        "Tkinter is required for the GUI.\n"
        "  Linux:           sudo apt install python3-tk\n"
        "  Windows / macOS: reinstall Python with 'tcl/tk and IDLE' enabled."
    ) from exc

from desktop_lifecycle import Autostart, create_tray, session_type
from desktop_lifecycle import App as Lifecycle

from .core import DEVICE_NAME
from .engine import Engine, sinks
from .diagnostics import save as save_diagnostics
from .i18n import t, detect_language, SUPPORTED

APP_NAME = 'ble-led-sync'
LIFECYCLE = Lifecycle(APP_NAME)
PATHS = LIFECYCLE.paths
CONFIG = PATHS.config / 'settings.json'

AUTOSTART = Autostart(
    APP_NAME,
    [str(Path(__file__).resolve().parent.parent / 'run.sh')],
    display_name='BLE LED Sync',
    comment='Local audio and screen sync',
    hidden_arg='--background',
)

MODES = ('SES', 'EKRAN', 'SES + EKRAN')
MODE_KEYS = {'SES': 'mode_audio', 'EKRAN': 'mode_screen', 'SES + EKRAN': 'mode_hybrid'}

def autostart_path():
    """Where the autostart entry lives; the library owns the format and mode."""
    return AUTOSTART.target

def set_autostart(enabled):
    """Enable or disable start-at-login. Raises when the entry could not be written."""
    if not (AUTOSTART.enable() if enabled else AUTOSTART.disable()):
        raise RuntimeError('Could not update the autostart entry.')

def open_folder(path):
    if _platform.system() == 'Windows': cmd = ['explorer', str(path)]
    elif _platform.system() == 'Darwin': cmd = ['open', str(path)]
    else: cmd = ['xdg-open', str(path)]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def build_tray(app):
    """The indicator menu: status line, the three modes, settings/stop/quit."""
    lang = app.lang.get()
    return create_tray(
        'BLE LED Sync',
        icon=str(Path(__file__).resolve().parent.parent / 'icon.svg'),
        items=[
            (t('mode_audio', lang), lambda: app.start('SES')),
            (t('mode_screen', lang), lambda: app.start('EKRAN')),
            (t('mode_hybrid', lang), lambda: app.start('SES + EKRAN')),
            None,  # separator
            (t('menu_settings', lang), app.show),
            (t('btn_stop', lang), app.stop),
            (t('menu_quit', lang), app.close),
        ],
    )

class App:
    def __init__(self,root,background=False):
        self.root=root; self.closing=False; self.running=False; self.tray=None
        self.messages={}; self.notice=''; self.save_job=None; self.engine=Engine()
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',font=('Sans',10),background='#17212b',foreground='#edf3f8')
        style.configure('TFrame',background='#17212b'); style.configure('TLabel',background='#17212b')
        style.configure('TCheckbutton',background='#17212b'); style.configure('TButton',padding=(10,7))
        root.configure(bg='#17212b')
        root.title('BLE LED Sync'); root.geometry('440x392'); root.minsize(410,370)
        self.lang=tk.StringVar(value=self._load_lang())
        self.mode=tk.StringVar(value='SES'); self.brightness=tk.DoubleVar(value=45); self.sensitivity=tk.DoubleVar(value=100)
        self.mode_display=tk.StringVar(value=self._mode_label('SES'))
        self.status=tk.StringVar(value=t('status_starting',self.lang.get())); self.auto=tk.BooleanVar(value=AUTOSTART.enabled)
        self.crop=True; self.monitor=1; self.sink='AUTO'; self.device_name=DEVICE_NAME
        self.load()
        f=ttk.Frame(root,padding=18); f.pack(fill='both',expand=True)
        top=ttk.Frame(f); top.pack(fill='x')
        ttk.Label(top,text='BLE LED SYNC',font=('Sans',17,'bold')).pack(side='left')
        self.lang_box=ttk.Combobox(top,textvariable=self.lang,values=list(SUPPORTED),state='readonly',width=4)
        self.lang_box.pack(side='right',padx=(0,6)); self.lang_box.bind('<<ComboboxSelected>>',lambda *_:self._on_lang_change())
        self.tools=ttk.Menubutton(top,text='⋯'); self.tools.pack(side='right')
        self.menu=tk.Menu(self.tools,tearoff=False); self.tools.configure(menu=self.menu)
        self.menu.add_command(label=t('menu_settings',self.lang.get()),command=self.advanced)
        self.menu.add_command(label=t('menu_test_red',self.lang.get()),command=self.test_red)
        self.menu.add_command(label=t('menu_diagnose',self.lang.get()),command=self.diagnose)
        self.menu.add_command(label=t('menu_logs',self.lang.get()),command=self.logs)
        self.menu.add_separator(); self.menu.add_command(label=t('menu_quit',self.lang.get()),command=self.close)
        self.lbl_status=ttk.Label(f,textvariable=self.status,wraplength=395,foreground='#b4c7d9')
        self.lbl_status.pack(anchor='w',pady=(8,12))
        self.mode_combo=ttk.Combobox(f,textvariable=self.mode_display,values=self._mode_labels(),state='readonly')
        self.mode_combo.pack(fill='x'); self.mode_combo.bind('<<ComboboxSelected>>',lambda *_:self._on_mode_select())
        self.scale_labels={}
        for key,var,lo,hi in (('label_brightness',self.brightness,0,100),('label_sensitivity',self.sensitivity,25,300)):
            row=ttk.Frame(f); row.pack(fill='x',pady=(12,0))
            title=ttk.Label(row,text=t(key,self.lang.get()),width=12); title.pack(side='left')
            self.scale_labels[key]=title
            ttk.Scale(row,from_=lo,to=hi,variable=var,command=lambda *_:self.options()).pack(side='left',fill='x',expand=True)
            val=ttk.Label(row,width=5); val.pack(side='right')
            var.trace_add('write',lambda *_,v=var,l=val:l.configure(text=f'%{v.get():.0f}'))
            val.configure(text=f'%{var.get():.0f}')
        self.chk_autostart=ttk.Checkbutton(f,text=t('chk_autostart',self.lang.get()),variable=self.auto,command=self.auto_changed)
        self.chk_autostart.pack(anchor='w',pady=(14,8))
        row=ttk.Frame(f); row.pack(fill='x')
        self.btn_start=ttk.Button(row,text=t('btn_start',self.lang.get()),command=lambda:self.start(self.mode.get()))
        self.btn_start.pack(side='left',padx=(0,7))
        self.btn_stop=ttk.Button(row,text=t('btn_stop',self.lang.get()),command=self.stop); self.btn_stop.pack(side='left')
        self.btn_hide=ttk.Button(row,text=t('btn_hide',self.lang.get()),command=self.hide); self.btn_hide.pack(side='right')
        self.lbl_hint=ttk.Label(f,text=t('hybrid_hint',self.lang.get()),foreground='#9db0c3'); self.lbl_hint.pack(anchor='w',pady=(10,0))
        try: self.tray=build_tray(self)
        except Exception:
            logging.exception('Tray failed to start')
            self.notice=t('msg_tray_unavailable',self.lang.get())
        root.protocol('WM_DELETE_WINDOW',self.hide)
        root.after(100,self.poll)
        self.start('SES')
        if background and self.tray: root.withdraw()
        elif background: root.deiconify()

    def _screen_supported(self):
        if _platform.system() in ('Windows', 'Darwin'):
            return True
        return session_type() == 'x11'

    def _load_lang(self):
        try:
            d=json.loads(CONFIG.read_text())
            lang=d.get('language')
            if lang in SUPPORTED: return lang
        except (OSError,ValueError,TypeError): pass
        return detect_language()

    def _mode_label(self,key):
        return t(MODE_KEYS[key],self.lang.get())

    def _mode_labels(self):
        return [self._mode_label(k) for k in MODES]

    def _label_to_mode(self,label):
        for k in MODES:
            if self._mode_label(k)==label: return k
        return 'SES'

    def _on_mode_select(self):
        key=self._label_to_mode(self.mode_display.get())
        self.mode.set(key)
        self.start(key)

    def _on_lang_change(self):
        self.save_settings()
        self.retranslate()

    def retranslate(self):
        lang=self.lang.get()
        self.mode_combo.configure(values=self._mode_labels())
        self.mode_display.set(self._mode_label(self.mode.get()))
        for key,widget in self.scale_labels.items():
            widget.configure(text=t(key,lang))
        self.chk_autostart.configure(text=t('chk_autostart',lang))
        self.btn_start.configure(text=t('btn_start',lang))
        self.btn_stop.configure(text=t('btn_stop',lang))
        self.btn_hide.configure(text=t('btn_hide',lang))
        self.lbl_hint.configure(text=t('hybrid_hint',lang))
        for index,key in ((0,'menu_settings'),(1,'menu_test_red'),(2,'menu_diagnose'),(3,'menu_logs'),(5,'menu_quit')):
            self.menu.entryconfigure(index,label=t(key,lang))
        if self.running:
            self.status.set(t('status_connecting',lang).format(mode=self._mode_label(self.mode.get())))
        else:
            self.status.set(t('status_starting',lang))

    def load(self):
        try:
            d=json.loads(CONFIG.read_text())
            self.brightness.set(max(0,min(100,float(d.get('brightness',45)))))
            self.sensitivity.set(max(25,min(300,float(d.get('sensitivity',100)))))
            lang=d.get('language')
            if lang in SUPPORTED: self.lang.set(lang)
            name=d.get('device_name')
            if isinstance(name,str) and name.strip(): self.device_name=name.strip()
        except (OSError,ValueError,TypeError): pass

    def options(self):
        self.engine.update(brightness=self.brightness.get()/100,sensitivity=self.sensitivity.get()/100,
                           crop=self.crop,monitor=self.monitor,sink=self.sink,name=self.device_name)
        if self.save_job is not None: self.root.after_cancel(self.save_job)
        self.save_job=self.root.after(700,self.save_settings)

    def start(self,mode):
        if mode!='SES' and not self._screen_supported():
            self.show(); messagebox.showwarning(t('mode_screen',self.lang.get()),t('warn_screen_wayland',self.lang.get())); return
        self.mode.set(mode); self.mode_display.set(self._mode_label(mode)); self.options()
        self.engine.update(mode=mode,active=True,want_ble=True,manual=None)
        self.running=True; self.status.set(t('status_connecting',self.lang.get()).format(mode=self._mode_label(mode)))

    def stop(self):
        self.running=False; self.engine.stop(); self.status.set(t('status_stopped',self.lang.get()))

    def test_red(self):
        self.options(); self.engine.update(active=False,want_ble=True,manual=(255,0,0))
        self.running=True; self.status.set(t('status_test_red',self.lang.get()))

    def show(self):
        self.root.deiconify(); self.root.lift()

    def hide(self):
        if self.tray: self.root.withdraw()
        else: self.root.iconify()
        # Without a tray the window is only minimized: never an orphan background process.

    def auto_changed(self):
        try: set_autostart(self.auto.get())
        except Exception as e:
            self.auto.set(AUTOSTART.enabled); messagebox.showerror(t('autostart_title',self.lang.get()),str(e))

    def advanced(self):
        lang=self.lang.get()
        w=tk.Toplevel(self.root); w.title(t('advanced_title',lang)); w.geometry('490x330')
        w.transient(self.root)
        mapping={t('advanced_auto_output',lang):'AUTO'}
        try:
            for s in sinks(): mapping[s.get('description',s['name'])+' ['+s['name']+']']=s['name']
        except Exception as e: logging.warning('Audio devices: %s',e)
        selected=tk.StringVar(value=next((k for k,v in mapping.items() if v==self.sink),next(iter(mapping))))
        ttk.Label(w,text=t('advanced_audio',lang)).pack(anchor='w',padx=15,pady=(15,5))
        ttk.Combobox(w,textvariable=selected,values=list(mapping),state='readonly',width=58).pack(padx=15)
        name_var=tk.StringVar(value=self.device_name)
        nrow=ttk.Frame(w); nrow.pack(fill='x',padx=15,pady=(10,0))
        ttk.Label(nrow,text=t('advanced_device',lang)).pack(side='left')
        ttk.Entry(nrow,textvariable=name_var).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Label(w,text=t('advanced_device_hint',lang),foreground='#6b7c8d').pack(anchor='w',padx=15,pady=(2,0))
        crop=tk.BooleanVar(value=self.crop); monitor=tk.IntVar(value=self.monitor)
        ttk.Checkbutton(w,text=t('advanced_crop',lang),variable=crop).pack(anchor='w',padx=15,pady=8)
        row=ttk.Frame(w); row.pack(fill='x',padx=15)
        ttk.Label(row,text=t('advanced_monitor',lang)).pack(side='left')
        ttk.Spinbox(row,from_=1,to=8,textvariable=monitor,width=4).pack(side='left',padx=8)
        def apply():
            try: self.monitor=max(1,int(monitor.get()))
            except (ValueError,tk.TclError): return
            self.crop=crop.get(); self.sink=mapping[selected.get()]
            self.device_name=name_var.get().strip() or DEVICE_NAME
            self.options(); w.destroy()
        ttk.Button(row,text=t('advanced_apply',lang),command=apply).pack(side='right')

    def diagnose(self):
        def worker():
            try: self.engine.events.put(('report',str(save_diagnostics())))
            except Exception as e: self.engine.events.put(('log',str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def logs(self):
        open_folder(PATHS.logs)

    def poll(self):
        if self.closing: return
        if self.tray:
            try: self.tray.pump()
            except Exception: logging.exception('Tray events')
        if LIFECYCLE.poll_show_request(): self.show()
        for _ in range(100):
            try: kind,value=self.engine.events.get_nowait()
            except queue.Empty: break
            if kind in ('ble','audio','screen','signal'):
                self.messages[kind]=value
            elif kind=='report':
                self.show(); messagebox.showinfo(t('diag_report',self.lang.get()),value+'\n\n'+t('diag_report_note',self.lang.get()))
        if self.running:
            errors=[v for k,v in self.messages.items() if ('error' in v.lower() or 'waiting' in v.lower() or 'connecting' in v.lower()) and
                    (k=='ble' or k=='signal' or (k=='audio' and self.mode.get()!='EKRAN') or (k=='screen' and self.mode.get()!='SES'))]
            detail=errors[0] if errors else self.messages.get('ble',t('status_connecting',self.lang.get()).format(mode=self._mode_label(self.mode.get())))
            self.status.set(self.mode.get()+' • '+(self.notice or detail))
        if self.tray: self.tray.set_label(self.status.get()[:100])
        self.root.after(80,self.poll)

    def save_settings(self):
        self.save_job=None
        try:
            CONFIG.parent.mkdir(parents=True,exist_ok=True)
            d=dict(brightness=self.brightness.get(),sensitivity=self.sensitivity.get(),
                   language=self.lang.get(),device_name=self.device_name)
            tmp=CONFIG.with_suffix('.tmp'); tmp.write_text(json.dumps(d),encoding='utf-8'); tmp.replace(CONFIG)
        except Exception: logging.exception('Settings save')

    def close(self):
        if self.closing: return
        self.closing=True
        if self.save_job is not None: self.root.after_cancel(self.save_job)
        self.save_settings()
        self.engine.close(); self.deadline=time.monotonic()+15; self.wait_close()

    def wait_close(self):
        if not any(t.is_alive() for t in self.engine.threads) or time.monotonic()>self.deadline: self.root.destroy()
        else: self.root.after(100,self.wait_close)

def main():
    LIFECYCLE.ensure_dirs()
    LIFECYCLE.setup_logging(filename='uygulama.log')
    root=tk.Tk(); root.withdraw()
    if not LIFECYCLE.acquire():
        # Another copy is running; it has been asked to show its window.
        root.destroy(); return
    try:
        app=App(root,background='--background' in sys.argv)
        if '--background' not in sys.argv: root.deiconify()
        root.mainloop()
    finally:
        LIFECYCLE.release()

if __name__=='__main__': main()
