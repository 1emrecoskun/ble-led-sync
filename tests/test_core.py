import unittest
import numpy as np
from led_sync.core import *

class ProtocolTests(unittest.TestCase):
    def test_power(self): self.assertEqual(POWER_ON.hex(),'7eff0401ffffffffef')
    def test_red(self): self.assertEqual(rgb_packet((255,0,0)).hex(),'7eff0503ff0000ffef')
    def test_black(self): self.assertEqual(rgb_packet((0,0,0)),bytes.fromhex('7E FF 05 03 00 00 00 FF EF'))
    def test_bounds(self): self.assertEqual(rgb_packet((-9,300,1.3))[4:7],bytes([0,255,1]))
    def test_nan(self):
        with self.assertRaises(ValueError): rgb_packet((float('nan'),0,0))
    def test_length(self):
        with self.assertRaises(ValueError): rgb_packet((0,0))
    def test_uuid(self): self.assertEqual(CHAR_UUID,'0000ffe1-0000-1000-8000-00805f9b34fb')

class SignalTests(unittest.TestCase):
    def tone(self,f): return .1*np.sin(2*np.pi*f*np.arange(4096)/22050)
    def test_silence(self): self.assertEqual(audio_features(np.zeros(2048)),((0.,0.,0.),0.))
    def test_short(self): self.assertEqual(audio_features([1,2]),((0.,0.,0.),0.))
    def test_bass(self): self.assertEqual(np.argmax(audio_features(self.tone(100))[0]),0)
    def test_mid(self): self.assertEqual(np.argmax(audio_features(self.tone(700))[0]),1)
    def test_high(self): self.assertEqual(np.argmax(audio_features(self.tone(4000))[0]),2)
    def test_sensitivity(self):
        self.assertLess(audio_features(self.tone(700),sensitivity=.5)[1],audio_features(self.tone(700),sensitivity=1)[1])
    def test_nans(self): self.assertEqual(audio_features(np.full(100,np.nan)),((0.,0.,0.),0.))
    def test_dc(self): self.assertEqual(audio_features(np.ones(100)),((0.,0.,0.),0.))
    def test_black_screen(self): self.assertEqual(dominant_rgb(np.zeros((10,10,3))), (0.,0.,0.))
    def test_red_screen(self): self.assertEqual(dominant_rgb(np.full((10,10,3),(255,0,0))), (255.,0.,0.))
    def test_black_borders(self):
        x=np.zeros((10,10,3),dtype=np.uint8); x[4:6,4:6]=(0,255,0)
        self.assertEqual(dominant_rgb(x),(0.,255.,0.))
    def test_dominance(self):
        x=np.array([[255,0,0]]*8+[[0,0,255]]*2)
        self.assertEqual(dominant_rgb(x),(255.,0.,0.))
    def test_hybrid_hue(self):
        rgb=combine('SES + EKRAN',(200,100,50),(0,0,255),.5)
        self.assertAlmostEqual(rgb[0]/rgb[1],2)
        self.assertAlmostEqual(rgb[1]/rgb[2],2)
    def test_hybrid_silence(self): self.assertEqual(combine('SES + EKRAN',(200,100,0),(0,0,0),0),(70.,35.,0.))
    def test_modes(self):
        self.assertEqual(combine('SES',(1,2,3),(4,5,6),1),(4,5,6))
        self.assertEqual(combine('EKRAN',(1,2,3),(4,5,6),1),(1,2,3))
    def test_smooth(self): self.assertEqual(smooth((0,0,0),(100,50,0),.2),(20.,10.,0.))
    def test_dedup(self): self.assertFalse(should_send((10,20,30),(11,21,30),.1))
    def test_keepalive(self): self.assertTrue(should_send((10,20,30),(10,20,30),4))
    def test_change(self): self.assertTrue(should_send((0,0,0),(4,0,0),.1))
    def test_first(self): self.assertTrue(should_send(None,(0,0,0),0))
    def test_wayland_over_display(self): self.assertEqual(session_type({'DISPLAY':':0','WAYLAND_DISPLAY':'wayland-0'}),'wayland')
    def test_x11(self): self.assertEqual(session_type({'DISPLAY':':0'}),'x11')
    def test_unknown(self): self.assertEqual(session_type({}),'unknown')

if __name__=='__main__': unittest.main()
