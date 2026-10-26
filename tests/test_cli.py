import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class CliTests(unittest.TestCase):
    def call(self,*args,ok=True):
        result=subprocess.run([sys.executable,'-m','strange_forge',*map(str,args)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0 if ok else 2,result.stderr)
        return json.loads(result.stdout if ok else result.stderr)
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            save=Path(d)/'harbor.save.json'
            self.call('new',save,'--name','Harbor Lights')
            self.call('add-character',save,'beacon','--name','Beacon','--hp',20,'--energy',10)
            proposal=self.call('propose',save,'brace-1',ROOT/'examples/brace-proposal.json')
            self.assertEqual(proposal['characters']['beacon']['energy'],10)
            state=self.call('complete',save,'brace-1')
            self.assertEqual((state['revision'],state['characters']['beacon']['energy'],state['characters']['beacon']['actions']),(3,8,2))
            self.call('complete',save,'brace-1',ok=False)
            self.assertEqual(self.call('show',save),state)
            self.assertTrue(self.call('validate',save)['valid'])
            receipt=self.call('roll','3d6+2'); self.assertEqual(receipt['total'],sum(receipt['dice'])+2)
            outcome=self.call('check','--dice',4,3,2,'--modifier',2,'--tc',11,'--tie-policy','success')
            self.assertTrue(outcome['success']); self.assertEqual(outcome['margin'],0)
    def test_bad_input_is_json_error(self):
        result=self.call('roll','__import__("os")',ok=False)
        self.assertIn('error',result)
