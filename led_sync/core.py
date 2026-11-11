"""Saf protokol ve renk işlevleri; donanım erişimi yoktur."""
import math
import numpy as np

CHAR_UUID = '0000ffe1-0000-1000-8000-00805f9b34fb'
DEVICE_NAME = 'LEDBLE-0D6183'
POWER_ON = bytes.fromhex('7E FF 04 01 FF FF FF FF EF')

def byte(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Geçersiz renk değeri')
    return max(0, min(255, round(value)))

def rgb_packet(rgb):
    if len(rgb) != 3:
        raise ValueError('Üç renk kanalı gerekir')
    return bytes([0x7E, 0xFF, 0x05, 0x03, *(byte(v) for v in rgb), 0xFF, 0xEF])

def audio_features(samples, rate=22050, sensitivity=1.0):
    x = np.asarray(samples, dtype=np.float32)
    if x.size < 32:
        return (0., 0., 0.), 0.
    x = np.nan_to_num(x, nan=0., posinf=0., neginf=0.)
    x = x - x.mean()
    rms = float(np.sqrt(np.mean(x*x)))
    if rms < 0.0008:
        return (0., 0., 0.), 0.
    spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    hz = np.fft.rfftfreq(len(x), 1/rate)
    bands = []
    for lo, hi in ((40, 250), (250, 2000), (2000, 8000)):
        part = spectrum[(hz >= lo) & (hz < hi)]
        bands.append(float(np.sqrt(np.sum(part*part))))
    peak = max(max(bands), 1e-9)
    energy = min(1., max(0., rms * 12 * sensitivity))
    return tuple(v/peak*255*energy for v in bands), energy

def dominant_rgb(pixels):
    """RGB dizi → 16 seviyeli histogram. Siyahlar dışlanır, siyah kare siyah döner."""
    p = np.asarray(pixels, dtype=np.uint8).reshape(-1, 3)
    if not len(p):
        return (0., 0., 0.)
    p = p[np.max(p, axis=1) > 16]
    if not len(p):
        return (0., 0., 0.)
    q = p.astype(np.int32) // 16
    keys = q[:, 0]*256 + q[:, 1]*16 + q[:, 2]
    winning = int(np.argmax(np.bincount(keys, minlength=4096)))
    return tuple(float(v) for v in p[keys == winning].mean(axis=0))

def combine(mode, screen, audio, energy):
    if mode == 'SES':
        return tuple(audio)
    if mode == 'EKRAN':
        return tuple(screen)
    # Hibritte ses renk tonunu değiştirmez; yalnız parlaklığı %35–100 arası etkiler.
    return tuple(v * (0.35 + 0.65 * max(0., min(1., energy))) for v in screen)

def smooth(previous, target, alpha=0.22):
    return tuple(a + (b-a)*alpha for a, b in zip(previous, target))

def should_send(previous, current, elapsed, threshold=4, keepalive=3.):
    return previous is None or max(abs(a-b) for a,b in zip(previous,current)) >= threshold or elapsed >= keepalive

def session_type(env):
    value = env.get('XDG_SESSION_TYPE', '').lower()
    if value == 'wayland' or env.get('WAYLAND_DISPLAY'):
        return 'wayland'
    if value == 'x11' or env.get('DISPLAY'):
        return 'x11'
    return 'unknown'

class BeatEnvelope:
    """Düşük gecikmeli bas/enerji atağı. Tempo veya kusursuz beat tracking değildir."""
    def __init__(self):
        self.baseline = 0.004
        self.previous_bass = 0.
        self.previous_rms = 0.
        self.pulse = 0.
        self.since_hit = 1.

    def update(self, samples, rate=22050, sensitivity=1.):
        x = np.nan_to_num(np.asarray(samples,dtype=np.float32),nan=0.,posinf=0.,neginf=0.)
        if len(x)<32: return 0.
        x = x-x.mean()
        dt = len(x)/rate
        rms = float(np.sqrt(np.mean(x*x)))
        spec = np.abs(np.fft.rfft(x*np.hanning(len(x))))
        hz = np.fft.rfftfreq(len(x),1/rate)
        bass = float(np.sqrt(np.sum(spec[(hz>=40)&(hz<250)]**2)) / len(x))
        rise = max(0.,bass-self.previous_bass*1.06, (rms-self.previous_rms*1.10)*0.35)
        score = rise / max(0.004,self.baseline*0.85) * sensitivity
        self.since_hit += dt
        self.pulse *= math.exp(-dt/0.14)
        if rms > 0.0015 and score>0.35 and self.since_hit>=0.08:
            self.pulse = max(self.pulse,min(1.,score))
            self.since_hit=0.
        a = 1-math.exp(-dt/1.0)
        self.baseline += a*(bass-self.baseline)
        self.previous_bass,self.previous_rms = bass,rms
        if rms<0.0008: self.pulse *= 0.4
        return self.pulse

def hybrid_pulse(screen,pulse):
    factor = 0.42 + 0.58*max(0.,min(1.,pulse))
    return tuple(v*factor for v in screen)
