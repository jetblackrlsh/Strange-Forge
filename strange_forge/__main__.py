import argparse
import json
import sys
from pathlib import Path
from . import ledger, dice, reference


def main():
    parser=argparse.ArgumentParser(description='Strange Forge — local, source-grounded GM tools')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('roll'); p.add_argument('expression')
    p=sub.add_parser('check'); p.add_argument('--dice',type=int,nargs=3,required=True); p.add_argument('--modifier',type=int,default=0); p.add_argument('--tc',type=int,required=True); p.add_argument('--tie-policy',choices=['success','failure'],required=True); p.add_argument('--actor',choices=['pc','npc'],default='pc',help='award proposals apply only to PC checks')
    p=sub.add_parser('index'); p.add_argument('source'); p.add_argument('output')
    p=sub.add_parser('search'); p.add_argument('index'); p.add_argument('query'); p.add_argument('--limit',type=int,default=5)
    p=sub.add_parser('new'); p.add_argument('save'); p.add_argument('--name',required=True)
    p=sub.add_parser('show'); p.add_argument('save')
    p=sub.add_parser('add-character'); p.add_argument('save'); p.add_argument('id'); p.add_argument('--name',required=True); p.add_argument('--hp',type=int,required=True); p.add_argument('--energy',type=int,required=True); p.add_argument('--nexus',type=int,default=0)
    p=sub.add_parser('propose'); p.add_argument('save'); p.add_argument('id'); p.add_argument('proposal',help='JSON file: reason, citations[], effects[]')
    for name in ['complete','cancel']:
        p=sub.add_parser(name); p.add_argument('save'); p.add_argument('id')
    p=sub.add_parser('validate'); p.add_argument('save')
    args=parser.parse_args()
    try:
        if args.command=='roll': result=dice.roll(args.expression)
        elif args.command=='check': result=dice.assess_check(args.dice,args.modifier,args.tc,tie_policy=args.tie_policy,actor=args.actor)
        elif args.command=='index':
            index=reference.build_index(args.source,args.output); result={'indexed':args.output,'pages':len(index['pages'])}
        elif args.command=='search': result=reference.search_index(reference.load_index(args.index),args.query,args.limit)
        elif args.command=='new': result=ledger.save(args.save,ledger.new_campaign(args.name))
        else:
            state=ledger.load(args.save); revision=state['revision']
            if args.command in ['show','validate']: result=state if args.command=='show' else {'valid':True,'revision':revision}
            else:
                if args.command=='add-character':
                    if args.id in state['characters']: raise ValueError('character already exists')
                    state['characters'][args.id]=ledger.character(args.name,args.hp,args.energy,args.nexus); state['revision']+=1; result=state
                elif args.command=='propose':
                    proposal=json.loads(Path(args.proposal).read_text(encoding='utf-8'))
                    if set(proposal)!={'reason','citations','effects'}: raise ValueError('proposal requires reason, citations, effects')
                    result=ledger.propose(state,args.id,**proposal)
                else: result=ledger.resolve(state,args.id,args.command=='complete')
                ledger.save(args.save,result,revision)
        print(json.dumps(result,indent=2,ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr); return 2
    return 0

if __name__=='__main__': sys.exit(main())
