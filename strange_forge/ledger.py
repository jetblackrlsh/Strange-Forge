"""Bounded, GM-adjudicated campaign ledger. No rules inference or network I/O."""
from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile
from contextlib import contextmanager

SCHEMA = 1


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label}: expected integer {low}..{high}')


def text(value, label, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{label}: expected nonempty text up to {limit} chars')


def new_campaign(name):
    state = dict(schema_version=SCHEMA, revision=0, name=name, characters={},
                 relationships={}, clocks={}, facts=[], transactions={}, events=[], gm_ego=0)
    validate(state)
    return state


def character(name, hp, energy, nexus=0):
    return dict(name=name, hp=hp, hp_max=hp, energy=energy, energy_max=energy,
                actions=3, actions_max=3, reactions=1, reactions_max=1,
                frustration=0, frustration_max=3+nexus, nexus=nexus,
                gold=0, conditions=[], inventory={})


def validate(state):
    keys={'schema_version','revision','name','characters','relationships','clocks','facts','transactions','events','gm_ego'}
    if not isinstance(state, dict) or set(state)!=keys or type(state['schema_version']) is not int or state['schema_version'] != SCHEMA:
        raise ValueError('unsupported or malformed campaign schema')
    integer(state['gm_ego'],0,10**6,'gm_ego'); integer(state['revision'],0,10**9,'revision'); text(state['name'],'name',200)
    for field, limit in [('characters',100),('relationships',200),('clocks',100),('transactions',1000)]:
        if not isinstance(state[field],dict) or len(state[field])>limit: raise ValueError(f'invalid {field}')
        for key in state[field]: text(key,field+' id',100)
    expected={'name','hp','hp_max','energy','energy_max','actions','actions_max','reactions','reactions_max','frustration','frustration_max','nexus','gold','conditions','inventory'}
    for c in state['characters'].values():
        if not isinstance(c,dict) or set(c)!=expected: raise ValueError('invalid character fields')
        text(c['name'],'character name',200)
        for k in ['hp','energy','actions','reactions','frustration']:
            integer(c[k+'_max'],0,10**6,k+'_max'); integer(c[k],-c[k+'_max'] if k=='energy' else 0,c[k+'_max'],k)
        for k in ['nexus','gold']: integer(c[k],0,10**6,k)
        if c['frustration_max'] != 3+c['nexus']: raise ValueError('frustration_max must equal 3+nexus')
        if not isinstance(c['conditions'],list) or len(c['conditions'])>100: raise ValueError('invalid conditions')
        for v in c['conditions']: text(v,'condition',200)
        if not isinstance(c['inventory'],dict) or len(c['inventory'])>200: raise ValueError('invalid inventory')
        for k,v in c['inventory'].items(): text(k,'item',200); integer(v,0,10**6,'quantity')
    for v in state['relationships'].values(): text(v,'relationship')
    for c in state['clocks'].values():
        if not isinstance(c,dict) or set(c)!={'value','max','description'}: raise ValueError('invalid clock')
        integer(c['max'],1,1000,'clock max'); integer(c['value'],0,c['max'],'clock value'); text(c['description'],'clock description')
    for field,limit in [('facts',500),('events',2000)]:
        if not isinstance(state[field],list) or len(state[field])>limit: raise ValueError(f'invalid {field}')
        for v in state[field]: text(v,field,4000)
    for tid,t in state['transactions'].items():
        if not isinstance(t,dict) or set(t)!={'status','reason','citations','effects'} or t['status'] not in ['proposed','completed','cancelled']: raise ValueError('invalid transaction')
        text(t['reason'],'reason',2000)
        if not isinstance(t['citations'],list) or not 1<=len(t['citations'])<=20: raise ValueError('citation/ruling required')
        for v in t['citations']: text(v,'citation',500)
        if not isinstance(t['effects'],list) or not 1<=len(t['effects'])<=100: raise ValueError('invalid effects')
        for e in t['effects']: _check_effect(e)
    # Reject NaN, non-JSON objects, giant payloads, and malformed nested values.
    if len(json.dumps(state,allow_nan=False))>2_000_000: raise ValueError('campaign too large')
    return state


def _check_effect(e):
    if not isinstance(e,dict) or set(e)!={'path','op','value'} or e['op'] not in ['set','delta']: raise ValueError('invalid effect')
    p=e['path']
    if not isinstance(p,list) or not 1<=len(p)<=4 or any(not isinstance(k,str) for k in p): raise ValueError('invalid path')
    allowed=(len(p)==3 and p[0]=='characters' and p[2] in {'hp','energy','actions','reactions','frustration','gold','conditions'}) or (len(p)==4 and p[0]=='characters' and p[2]=='inventory') or (len(p)==2 and p[0]=='relationships') or (len(p)==3 and p[0]=='clocks' and p[2]=='value') or (p in [['facts'],['gm_ego']])
    if not allowed: raise ValueError('effect path is not mutable; edit setup explicitly')
    if e['op']=='delta' and type(e['value']) is not int: raise ValueError('delta must be integer')


def propose(state, tid, reason, citations, effects):
    result=deepcopy(state); text(tid,'transaction id',100)
    if tid in result['transactions']: raise ValueError('transaction id already exists')
    result['transactions'][tid]=dict(status='proposed',reason=reason,citations=citations,effects=effects)
    result['revision']+=1
    return validate(result)


def resolve(state, tid, complete=True):
    result=deepcopy(state)
    transaction=result['transactions'][tid]
    if transaction['status']!='proposed': raise ValueError('transaction already resolved')
    if complete:
        for effect in transaction['effects']:
            target=result
            for key in effect['path'][:-1]: target=target[key]
            key=effect['path'][-1]
            if effect['op']=='delta':
                if type(target.get(key,0)) is not int: raise ValueError('delta target must be integer')
                target[key]=target.get(key,0)+effect['value']
            else: target[key]=deepcopy(effect['value'])
    transaction['status']='completed' if complete else 'cancelled'
    result['events'].append(f'{tid}: {transaction["status"]}: {transaction["reason"]}')
    result['revision']+=1
    return validate(result)


def load(path):
    path=Path(path)
    if path.stat().st_size>2_000_000: raise ValueError('campaign too large')
    return validate(json.loads(path.read_text(encoding='utf-8')))


@contextmanager
def _lock(path):
    lock=Path(str(path)+'.lock')
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        os.write(fd,str(os.getpid()).encode()); os.close(fd); yield
    finally:
        lock.unlink(missing_ok=True)


def _replace_bytes(path,data):
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def save(path,state,expected_revision=None):
    """Atomic local write with previous-save .bak and optimistic concurrency.

    Creation requires expected_revision=None; updating requires current revision.
    A stale lock needs human review, never automatic deletion.
    """
    validate(state); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(state,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with _lock(path):
        if path.exists():
            current=load(path)
            if expected_revision is None or current['revision']!=expected_revision: raise ValueError('save conflict: reload campaign')
            if state['revision']<=current['revision']: raise ValueError('revision must advance')
            _replace_bytes(Path(str(path)+'.bak'),path.read_bytes())
        elif expected_revision is not None: raise ValueError('save conflict: campaign missing')
        _replace_bytes(path,data)
    return state
