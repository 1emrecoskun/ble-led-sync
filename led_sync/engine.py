import asyncio
import json
import logging
import os
import queue
import select
import subprocess
import threading
import time
import numpy as np
from .core import (CHAR_UUID, DEVICE_NAME, POWER_ON, rgb_packet, audio_features,
                   dominant_rgb, combine, smooth, should_send, session_type, byte, BeatEnvelope, hybrid_pulse)

log = logging.getLogger(__name__)

def command(args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=4,
                       env={**os.environ, 'LC_ALL':'C'})
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or f'{args[0]} çıkış={p.returncode}')
    return p.stdout.strip()

def sinks():
    return json.loads(command(['pactl','-f','json','list','sinks']))

def monitor_source(sink):
    if sink == 'AUTO':
        try: sink = command(['pactl','get-default-sink'])
        except RuntimeError:
            text = command(['pactl','info'])
            sink = next((x.split(': ',1)[1] for x in text.splitlines() if x.startswith('Default Sink: ')), '')
    all_sinks = sinks()
    found = next((s for s in all_sinks if s['name'] == sink), None)
    if found is None:
        raise RuntimeError('Selected audio output not found; try Automatic.')
    value = found.get('monitor_source_name', found.get('monitor_source'))
    sources = json.loads(command(['pactl','-f','json','list','sources']))
    for s in sources:
        if value is not None and (s.get('name') == value or s.get('index') == value):
            return s['name']
    candidate = sink + '.monitor'
    if any(s.get('name') == candidate for s in sources):
        return candidate
    raise RuntimeError('Monitor source for this output not found; not replaced with microphone.')

class Engine:
    def __init__(self):
        self.events = queue.Queue()
        self.lock = threading.Lock()
        self.shutdown = threading.Event()
        self.options = dict(active=False, want_ble=False, mode='SES', sink='AUTO',
                            brightness=0.45, sensitivity=1., crop=True, monitor=1,
                            name=DEVICE_NAME, write='Otomatik', manual=None)
        self.audio = ((0.,0.,0.), 0., 0.)
        self.beat = 0.
        self.screen = ((0.,0.,0.), 0.)
        self.last_messages = {}
        self.threads = [threading.Thread(target=self.audio_loop, daemon=True),
                        threading.Thread(target=self.screen_loop, daemon=True),
                        threading.Thread(target=lambda: asyncio.run(self.ble_loop()), daemon=True)]
        for t in self.threads: t.start()

    def emit(self, kind, text):
        if kind in ('audio','screen','ble') and self.last_messages.get(kind) == text:
            return
        self.last_messages[kind] = text
        log.info('%s: %s', kind, text)
        self.events.put((kind, text))

    def update(self, **values):
        with self.lock: self.options.update(values)

    def snapshot(self):
        with self.lock: return dict(self.options)

    def stop(self):
        self.update(active=False, want_ble=False, manual=None)

    def close(self):
        self.stop()
        self.shutdown.set()

    def audio_loop(self):
        proc, current, pending, check_at = None, None, b'', 0.
        detector=BeatEnvelope(); last_hybrid=None
        try:
            while not self.shutdown.is_set():
                o = self.snapshot()
                needed = o['active'] and o['mode'] in ('SES', 'SES + EKRAN')
                if not needed:
                    self._kill(proc); proc, current, pending = None, None, b''
                    self.shutdown.wait(.2); continue
                import platform as _pf
                if _pf.system() != 'Linux':
                    self.emit('audio','Audio capture not supported on this platform yet; use Screen mode.')
                    self.shutdown.wait(2); continue
                try:
                    hybrid=o['mode']=='SES + EKRAN'
                    latency=30 if hybrid else 60
                    frame_bytes=4096 if hybrid else 8192
                    if hybrid != last_hybrid:
                        self._kill(proc); proc,current,pending=None,None,b''
                        detector=BeatEnvelope(); last_hybrid=hybrid
                    if time.monotonic() >= check_at or proc is None:
                        source = monitor_source(o['sink'])
                        check_at = time.monotonic()+2
                        if source != current or proc is None or proc.poll() is not None:
                            self._kill(proc)
                            proc = subprocess.Popen(['parec','--raw','--format=float32le','--rate=22050',
                                                     '--channels=1','--latency-msec='+str(latency),'--device='+source],
                                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                            current, pending = source, b''
                            self.emit('audio','Audio output: '+source)
                    if proc.poll() is not None:
                        raise RuntimeError('parec kapandı; monitor kaynağı veya ses servisini kontrol edin.')
                    ready,_,_ = select.select([proc.stdout],[],[],.04 if hybrid else .15)
                    if not ready: continue
                    chunk = os.read(proc.stdout.fileno(), 8192)
                    if not chunk: raise RuntimeError('Ses akışı kapandı.')
                    pending += chunk
                    while len(pending) >= frame_bytes:
                        block, pending = pending[:frame_bytes], pending[frame_bytes:]
                        samples=np.frombuffer(block,dtype='<f4')
                        rgb, energy = audio_features(samples, sensitivity=o['sensitivity'])
                        if energy == 0. and rgb == (0., 0., 0.):
                            # Sessizlikte tamamen siyah yerine hafif bir temel renk:
                            # LED "kapalı/bozuk" görünmez, cihazın çalıştığı belli olur.
                            rgb = (18., 18., 36.)
                        beat=detector.update(samples,sensitivity=o['sensitivity']) if hybrid else 0.
                        with self.lock:
                            self.audio = (rgb, energy, time.monotonic())
                            self.beat = beat
                except Exception as e:
                    log.debug('Ses ayrıntısı',exc_info=True)
                    self.emit('audio','Audio error: '+str(e))
                    self._kill(proc); proc, current, pending = None, None, b''
                    with self.lock: self.audio = ((0.,0.,0.),0.,0.)
                    self.shutdown.wait(2)
        finally: self._kill(proc)

    @staticmethod
    def _kill(proc):
        if proc is not None:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(timeout=1)
            if proc.stdout: proc.stdout.close()

    def screen_loop(self):
        sct = None
        try:
            while not self.shutdown.is_set():
                o = self.snapshot()
                if not (o['active'] and o['mode'] in ('EKRAN','SES + EKRAN')):
                    if sct: sct.close(); sct = None
                    self.shutdown.wait(.2); continue
                try:
                    import platform as _pf
                    if _pf.system() == 'Linux' and session_type(os.environ) != 'x11':
                        raise RuntimeError('Screen capture in this version supports X11 only. Wayland portal not yet supported.')
                    if sct is None:
                        import mss
                        sct = mss.mss()
                    idx = int(o['monitor'])
                    if idx < 1 or idx >= len(sct.monitors):
                        raise RuntimeError('Screen number not found; choose 1.')
                    rect = dict(sct.monitors[idx])
                    if o['crop']:
                        dx,dy = int(rect['width']*.1),int(rect['height']*.1)
                        rect.update(left=rect['left']+dx,top=rect['top']+dy,
                                    width=rect['width']-2*dx,height=rect['height']-2*dy)
                    image = np.asarray(sct.grab(rect))
                    step = max(1, min(image.shape[:2])//64)
                    rgb = dominant_rgb(image[::step,::step,:3][:,:,::-1])
                    with self.lock: self.screen = (rgb,time.monotonic())
                    self.emit('screen','Capturing screen — X11, 5 fps')
                    self.shutdown.wait(.2)
                except Exception as e:
                    log.debug('Ekran ayrıntısı',exc_info=True)
                    self.emit('screen','Screen error: '+str(e))
                    with self.lock: self.screen = ((0.,0.,0.),0.)
                    if sct: sct.close(); sct=None
                    self.shutdown.wait(2)
        finally:
            if sct: sct.close()

    async def ble_loop(self):
        from bleak import BleakScanner, BleakClient
        last_address = None
        retry = 2
        while not self.shutdown.is_set():
            o = self.snapshot()
            if not o['want_ble']:
                await asyncio.sleep(.2); continue
            client = None
            try:
                target = o['name'].strip()
                if not target:
                    raise RuntimeError('Controller name cannot be empty.')
                # bluez'de asılı kalan bağlantıyı temizle (taramayı engeller).
                try:
                    out = subprocess.run(['bluetoothctl','devices'],capture_output=True,text=True,timeout=4).stdout
                    for line in out.splitlines():
                        parts = line.split(None,2)
                        if len(parts) >= 3 and parts[2].strip().casefold() == target.casefold():
                            addr = parts[1]
                            info = subprocess.run(['bluetoothctl','info',addr],capture_output=True,text=True,timeout=4).stdout
                            if 'Connected: yes' in info:
                                subprocess.run(['bluetoothctl','disconnect',addr],capture_output=True,text=True,timeout=6)
                            break
                except Exception:
                    pass
                self.emit('ble','Scanning: '+target)
                scanned = await BleakScanner.find_device_by_filter(
                    lambda d,a: (a.local_name or d.name or '').casefold() == target.casefold(), timeout=8)
                if not scanned:
                    raise RuntimeError('Device not found. LED on, Bluetooth on, phone app closed.')
                device = scanned
                last_address = getattr(scanned, 'address', None)
                if not self.snapshot()['want_ble'] or self.shutdown.is_set(): continue
                client = BleakClient(scanned, timeout=10)
                await client.connect()
                if not self.snapshot()['want_ble'] or self.shutdown.is_set(): continue
                chars = [c for s in client.services for c in s.characteristics if c.uuid.lower()==CHAR_UUID]
                if len(chars) != 1:
                    raise RuntimeError('ffe1 characteristic missing or multiple; not written randomly.')
                char = chars[0]
                if o['write'] == 'Yanıtlı': response=True
                elif o['write'] == 'Yanıtsız': response=False
                elif 'write-without-response' in char.properties: response=False
                elif 'write' in char.properties: response=True
                else: raise RuntimeError('Karakteristik yazma özelliği bildirmiyor.')
                required = 'write' if response else 'write-without-response'
                if required not in char.properties:
                    raise RuntimeError('Seçilen yazma türü cihazın bildirdiği özelliklerle uyumlu değil.')
                self.emit('log',f'GATT write type: {required}; properties: {char.properties}')
                await asyncio.wait_for(client.write_gatt_char(char,POWER_ON,response=response),timeout=3)
                self.emit('ble','Connected — verify color on the LED')
                retry=2; previous=None; filtered=(0.,0.,0.); screen_filtered=(0.,0.,0.); last_sent=0.
                while not self.shutdown.is_set() and self.snapshot()['want_ble']:
                    if not client.is_connected: raise RuntimeError('BLE bağlantısı koptu.')
                    o=self.snapshot(); now=time.monotonic()
                    with self.lock: audio,energy,at=self.audio; screen,st=self.screen; beat=self.beat
                    is_hybrid=o['mode']=='SES + EKRAN' and o['manual'] is None
                    interval=.06 if is_hybrid else .1
                    target_rgb=o['manual']
                    if target_rgb is None and o['active']:
                        need_audio=o['mode'] in ('SES','SES + EKRAN')
                        need_screen=o['mode'] in ('EKRAN','SES + EKRAN')
                        if (need_audio and now-at>2) or (need_screen and now-st>2):
                            self.emit('signal','Waiting for signal; check audio/screen.')
                            await asyncio.sleep(.1); continue
                        self.emit('signal','Signal received')
                        if is_hybrid:
                            # Ekran rengi ayrı yumuşar; ses atağı eski %22 filtresinde geciktirilmez.
                            screen_filtered=smooth(screen_filtered,screen,.40)
                            target_rgb=hybrid_pulse(screen_filtered,beat)
                        else:
                            target_rgb=combine(o['mode'],screen,audio,energy)
                    if target_rgb is None:
                        await asyncio.sleep(.1); continue
                    target_rgb=tuple(v*o['brightness'] for v in target_rgb)
                    filtered=target_rgb if is_hybrid else smooth(filtered,target_rgb)
                    rgb=tuple(byte(v) for v in filtered)
                    self.events.put(('preview',rgb))
                    if should_send(previous,rgb,now-last_sent):
                        if not self.snapshot()['want_ble']: break
                        await asyncio.wait_for(client.write_gatt_char(char,rgb_packet(rgb),response=response),timeout=3)
                        previous,last_sent=rgb,time.monotonic()
                    await asyncio.sleep(interval)
            except Exception as e:
                log.exception('BLE hata ayrıntısı')
                self.emit('ble','Connection error: '+str(e))
                if self.snapshot()['want_ble']:
                    self.emit('log',f'{retry} s until rescan; STOP cancels.')
                    for _ in range(retry*5):
                        if self.shutdown.is_set() or not self.snapshot()['want_ble']: break
                        await asyncio.sleep(.2)
                    retry=min(30,retry*2)
            finally:
                if client is not None:
                    try: await asyncio.wait_for(client.disconnect(),timeout=3)
                    except Exception: pass
                self.emit('ble','Connection closed' if not self.snapshot()['want_ble'] else 'Waiting for reconnect')
