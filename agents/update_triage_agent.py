#!/usr/bin/env python3
"""Triage candidate updates into ASI, lifecycle, tool, and roadmap impact."""
from __future__ import annotations
import argparse,json,datetime as dt,re
from pathlib import Path
from typing import Any,Dict,List
ROOT=Path(__file__).resolve().parents[1]
def load(p,default=None):
    path=ROOT/p
    return json.loads(path.read_text()) if path.exists() else default
def save(p,data):
    path=ROOT/p; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,ensure_ascii=False))
def now(): return dt.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
def norm(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def triage_update(u,tools):
    text=norm(' '.join([u.get('vendor_name',''),u.get('title',''),u.get('summary','')]))
    matched=[]
    for t in tools.get('tools',[]):
        names=[t.get('id',''),t.get('name',''),t.get('org','')]
        if any(norm(n) and norm(n) in text for n in names):
            matched.append(t.get('id'))
    if not matched:
        vid=u.get('vendor_id','')
        for t in tools.get('tools',[]):
            if vid and vid in norm(t.get('org','')+' '+t.get('id','')): matched.append(t.get('id'))
    recommendation='review_only'
    if u.get('priority') in ['critical','high'] and (u.get('candidate_asi') or matched): recommendation='create_evidence_candidate'
    if 'roadmap' in u.get('candidate_features',[]): recommendation='roadmap_update'
    return {**u,"matched_tools":sorted(set(matched))[:8],"recommended_action":recommendation,"review_questions":["Is this an official vendor/standard source?","Does the update change tool capability, risk coverage, roadmap, or evidence confidence?","Is a benchmark case or incident mapping needed?"],"triaged_at":now()}
def main(args):
    pending=load(args.input,{"updates":[]})
    tools=load('data/tools.json',{"tools":[]})
    triaged=[triage_update(u,tools) for u in pending.get('updates',[])]
    save(args.output,{"meta":{"version":"v1.0","generated_at":now()},"triaged_updates":triaged})
    status=load('data/updates/auto_update_status.json',{}) or {}
    status['triaged_updates']=len(triaged); status['updated']=now(); save('data/updates/auto_update_status.json',status)
    print(f"Triaged {len(triaged)} updates -> {args.output}")
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--input',default='data/updates/pending_updates.json'); ap.add_argument('--output',default='data/updates/triaged_updates.json'); main(ap.parse_args())
