#!/usr/bin/env python3
import argparse,json,xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--junit',required=True); p.add_argument('--expected',required=True); p.add_argument('--output',required=True); a=p.parse_args()
expected=json.loads(Path(a.expected).read_text())['tests']; root=ET.parse(a.junit).getroot(); cases=root.findall('.//testcase'); got=[]
for c in cases:
    name=c.get('name',''); cls=c.get('classname',''); ident=f'{cls.split(".")[-1]}.py::{name}'
    if c.find('failure') is not None or c.find('error') is not None or c.find('skipped') is not None: raise SystemExit(2)
    got.append(ident)
if len(got)!=len(set(got)) or set(got)!=set(expected): raise SystemExit(2)
Path(a.output).write_text(json.dumps({'tests':got,'count':len(got),'failures':0,'errors':0,'skipped':0},sort_keys=True)+'\n')
