import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from strange_forge import ledger as l

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.s=l.new_campaign('Fictional harbor')
        self.s['characters']['beacon']=l.character('Beacon',20,10)
        self.s['clocks']['storm']={'value':0,'max':4,'description':'Storm arrives'}
    def effect(self,field,value,op='delta'):
        return {'path':['characters','beacon',field],'op':op,'value':value}
    def test_power_turn_and_reload(self):
        p=l.propose(self.s,'power-1','GM approved shield; cost manually verified',['Original fictional custom power: 2 energy / 1 action'],[self.effect('energy',-2),self.effect('actions',-1)])
        self.assertEqual(p['characters']['beacon']['energy'],10)
        s=l.resolve(p,'power-1'); self.assertEqual(s['characters']['beacon']['energy'],8); self.assertEqual(s['characters']['beacon']['actions'],2)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'save.json'; l.save(path,self.s); l.save(path,p,0); l.save(path,s,1)
            self.assertEqual(l.load(path),s); self.assertEqual(l.load(str(path)+'.bak'),p)
        with self.assertRaises(ValueError): l.resolve(s,'power-1')
    def test_frustration_ego_and_nexus(self):
        self.s['characters']['beacon']=l.character('Beacon',20,10,2)
        effects=[self.effect('frustration',5),{'path':['gm_ego'],'op':'delta','value':1}]
        s=l.resolve(l.propose(self.s,'failure','Adjudicated failure and later success',['GM test ruling'],effects),'failure')
        self.assertEqual(s['characters']['beacon']['frustration'],5)
        self.assertEqual(s['gm_ego'],1)
    def test_invalid_is_atomic(self):
        p=l.propose(self.s,'bad','Unaffordable power',['GM test ruling'],[self.effect('energy',-21)])
        with self.assertRaises(ValueError): l.resolve(p,'bad')
        self.assertEqual(p['transactions']['bad']['status'],'proposed'); self.assertEqual(p['characters']['beacon']['energy'],10)
    def test_cancel(self):
        p=l.propose(self.s,'cancel','Declined purchase',['GM test ruling'],[self.effect('gold',-1)])
        s=l.resolve(p,'cancel',False); self.assertEqual(s['characters']['beacon']['gold'],0)
    def test_strict_schema(self):
        for field,value in [('hp',True),('energy',-11),('frustration',4),('gold',1.5)]:
            s=json.loads(json.dumps(self.s)); s['characters']['beacon'][field]=value
            with self.subTest(field=field), self.assertRaises(ValueError): l.validate(s)
    def test_lock_conflict_and_failed_replace(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'save.json'; l.save(path,self.s)
            p=l.propose(self.s,'x','test',['GM ruling'],[self.effect('hp',-1)])
            with self.assertRaises(ValueError): l.save(path,p,99)
            self.assertEqual(l.load(path),self.s)
            original=l._replace_bytes
            def fail_main(target,data):
                if target==path: raise OSError('simulated disk error')
                return original(target,data)
            with patch.object(l,'_replace_bytes',side_effect=fail_main), self.assertRaises(OSError): l.save(path,p,0)
            self.assertEqual(l.load(path),self.s); self.assertFalse(Path(str(path)+'.lock').exists())
            Path(str(path)+'.lock').write_text('manual lock')
            with self.assertRaises(FileExistsError): l.save(path,p,0)
    def test_restricted_effect(self):
        with self.assertRaises(ValueError): l.propose(self.s,'x','test',['GM ruling'],[{'path':['schema_version'],'op':'set','value':9}])
    def test_clock_inventory_relationship(self):
        effects=[{'path':['characters','beacon','inventory','rope'],'op':'delta','value':1},{'path':['clocks','storm','value'],'op':'delta','value':1},{'path':['relationships','dockkeeper'],'op':'set','value':'Trust earned'}]
        s=l.resolve(l.propose(self.s,'rescue','Completed rescue',['Original fictional example'],effects),'rescue')
        self.assertEqual(s['characters']['beacon']['inventory']['rope'],1)
        self.assertEqual(s['clocks']['storm']['value'],1)

    def test_negative_energy_and_gm_ego(self):
        effects=[self.effect('energy',-12),{'path':['gm_ego'],'op':'delta','value':1}]
        s=l.resolve(l.propose(self.s,'drain','GM resolved drain',['Strange Heroes v1.02 p22; GM award adjudicated'],effects),'drain')
        self.assertEqual(s['characters']['beacon']['energy'],-2)
        self.assertEqual(s['gm_ego'],1)

    def test_schema_boolean_and_failed_backup(self):
        bad=dict(self.s); bad['schema_version']=True
        with self.assertRaises(ValueError): l.validate(bad)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'save.json'; l.save(path,self.s)
            proposal=l.propose(self.s,'x','test',['GM ruling'],[self.effect('hp',-1)])
            with patch.object(l,'_replace_bytes',side_effect=OSError('backup failed')), self.assertRaises(OSError):
                l.save(path,proposal,0)
            self.assertEqual(l.load(path),self.s)
