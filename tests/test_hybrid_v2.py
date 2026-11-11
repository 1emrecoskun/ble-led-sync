import unittest
import numpy as np
from led_sync.core import BeatEnvelope, hybrid_pulse, smooth

class HybridV2Tests(unittest.TestCase):
    def block(self,amp,index=0):
        t=(np.arange(1024)+1024*index)/22050
        return amp*np.sin(2*np.pi*100*t)
    def warm(self,d):
        for i in range(50): d.update(self.block(.015,i))
    def test_silence(self): self.assertEqual(BeatEnvelope().update(np.zeros(1024)),0.)
    def test_fast_attack(self):
        d=BeatEnvelope(); self.warm(d)
        self.assertGreater(d.update(self.block(.25,50)),.8)
    def test_sustained_not_always_full(self):
        d=BeatEnvelope()
        values=[d.update(self.block(.25,i)) for i in range(80)]
        self.assertLess(max(values[-10:]),.1)
    def test_release(self):
        d=BeatEnvelope(); self.warm(d)
        peak=d.update(self.block(.25,50))
        end=peak
        for i in range(51,61): end=d.update(self.block(.015,i))
        self.assertLess(end,peak*.2)
    def test_repeated_hits(self):
        d=BeatEnvelope(); self.warm(d)
        for beat in range(3):
            self.assertGreater(d.update(self.block(.25,beat*20+50)),.5)
            for i in range(1,15): d.update(self.block(.015,beat*20+50+i))
    def test_preserve_hue(self):
        out=hybrid_pulse((200,100,50),.9)
        self.assertAlmostEqual(out[0]/out[1],2)
        self.assertAlmostEqual(out[1]/out[2],2)
    def test_background(self): self.assertEqual(hybrid_pulse((100,0,0),0),(42.,0.,0.))
    def test_peak(self): self.assertEqual(hybrid_pulse((100,20,0),1),(100.,20.,0.))
    def test_clamp(self): self.assertEqual(hybrid_pulse((100,20,0),5),hybrid_pulse((100,20,0),1))
    def test_sensitivity(self):
        a=BeatEnvelope(); b=BeatEnvelope(); self.warm(a); self.warm(b)
        self.assertGreaterEqual(b.update(self.block(.05,50),sensitivity=2),a.update(self.block(.05,50),sensitivity=.5))
    def test_nan(self): self.assertEqual(BeatEnvelope().update(np.full(1024,np.nan)),0.)
    def test_short(self): self.assertEqual(BeatEnvelope().update([0,1]),0.)
    def test_old_smoothing_delay_removed(self):
        screen=(200.,100.,50.)
        old=smooth(tuple(v*.42 for v in screen),screen)
        new=hybrid_pulse(screen,1)
        self.assertGreater(new[0],old[0])

if __name__=='__main__': unittest.main()
