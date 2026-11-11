import asyncio
import json
import sys
import threading
import types
import unittest
from unittest.mock import patch
from led_sync.engine import Engine, monitor_source
from led_sync.core import POWER_ON

class AudioSelectionTests(unittest.TestCase):
    def test_auto_monitor(self):
        def fake(args):
            if args==['pactl','get-default-sink']: return 'speaker'
            if args[-1]=='sinks': return json.dumps([{'name':'speaker','monitor_source':7}])
            return json.dumps([{'name':'mic','index':1},{'name':'speaker.monitor','index':7}])
        with patch('led_sync.engine.command',side_effect=fake): self.assertEqual(monitor_source('AUTO'),'speaker.monitor')
    def test_switch(self):
        for target in ['speaker','bluetooth']:
            def fake(args):
                if args==['pactl','get-default-sink']: return target
                if args[-1]=='sinks': return json.dumps([{'name':target,'monitor_source':target+'.monitor'}])
                return json.dumps([{'name':target+'.monitor'}])
            with patch('led_sync.engine.command',side_effect=fake): self.assertEqual(monitor_source('AUTO'),target+'.monitor')
    def test_no_mic_fallback(self):
        def fake(args):
            if args[-1]=='sinks': return json.dumps([{'name':'speaker'}])
            return json.dumps([{'name':'mic'}])
        with patch('led_sync.engine.command',side_effect=fake):
            with self.assertRaisesRegex(RuntimeError,'not replaced with microphone'): monitor_source('speaker')
    def test_missing_sink(self):
        with patch('led_sync.engine.command',return_value='[]'):
            with self.assertRaises(RuntimeError): monitor_source('missing')

class BleTests(unittest.IsolatedAsyncioTestCase):
    async def scenario(self, properties, write='Otomatik', cancel_scan=False):
        with patch.object(threading.Thread,'start'): engine=Engine()
        engine.update(want_ble=True,manual=(255,0,0),write=write)
        calls=[]; chosen=object()
        class Scanner:
            @staticmethod
            async def find_device_by_filter(predicate,timeout):
                assert predicate(types.SimpleNamespace(name='LEDBLE-0D6183'),types.SimpleNamespace(local_name=None))
                assert not predicate(types.SimpleNamespace(name='OTHER'),types.SimpleNamespace(local_name=None))
                if cancel_scan: engine.close()
                return chosen
        class Client:
            def __init__(self,device,timeout):
                assert device is chosen
                c=types.SimpleNamespace(uuid='0000ffe1-0000-1000-8000-00805f9b34fb',properties=properties)
                self.services=[types.SimpleNamespace(characteristics=[c])]; self.is_connected=False
            async def connect(self): self.is_connected=True
            async def disconnect(self): self.is_connected=False; calls.append(('disconnect',))
            async def write_gatt_char(self,char,data,response):
                calls.append((data,response))
                if data != POWER_ON: engine.close()
        fake=types.SimpleNamespace(BleakScanner=Scanner,BleakClient=Client)
        with patch.dict(sys.modules,{'bleak':fake}):
            try: await asyncio.wait_for(engine.ble_loop(),timeout=2)
            finally: engine.close()
        return calls
    async def test_no_response_flow(self):
        calls=await self.scenario(['write-without-response'])
        self.assertEqual(calls[0],(POWER_ON,False)); self.assertEqual(len(calls[1][0]),9)
        self.assertEqual(calls[-1],('disconnect',))
    async def test_response_flow(self): self.assertEqual((await self.scenario(['write']))[0],(POWER_ON,True))
    async def test_explicit_response(self): self.assertEqual((await self.scenario(['write','write-without-response'],'Yanıtlı'))[0],(POWER_ON,True))
    async def test_cancel_after_scan(self): self.assertEqual(await self.scenario(['write'],cancel_scan=True),[])

if __name__=='__main__': unittest.main()
