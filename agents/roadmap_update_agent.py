#!/usr/bin/env python3
"""Generate roadmap items and catalog patch suggestions from triaged updates."""
from __future__ import annotations
import argparse,json,datetime as dt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p,default=None):
    path=ROOT/p
    return json.loads(path.read_text()) if path.exists() else default
def save(p,data):
    path=ROOT/p; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,indent=2,ensure_ascii=False))
def now(): return dt.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
def main(args):
    triaged=load(args.input,{"triaged_updates":[]}).get('triaged_updates',[])
    roadmap=[]; suggestions=[]
    for u in triaged:
        if u.get('recommended_action')=='roadmap_update' or 'roadmap' in u.get('candidate_features',[]):
            roadmap.append({"id":"roadmap_"+u['id'],"title":u['title'],"vendor":u['vendor_name'],"url":u['url'],"priority":u['priority'],"signals":u.get('candidate_features',[]),"mapped_asi":u.get('candidate_asi',[]),"status":"needs_review","created_at":now()})
        if u.get('recommended_action')=='create_evidence_candidate':
            suggestions.append({"id":"patch_"+u['id'],"type":"evidence_candidate","title":u['title'],"vendor":u['vendor_name'],"matched_tools":u.get('matched_tools',[]),"url":u['url'],"candidate_asi":u.get('candidate_asi',[]),"candidate_lifecycle_stages":u.get('candidate_lifecycle_stages',[]),"suggested_change":"Add evidence record or update source_basis only after human validation.","status":"needs_review"})
    save(args.roadmap,{"meta":{"version":"v1.0","generated_at":now()},"roadmap_items":roadmap})
    save(args.suggestions,{"meta":{"version":"v1.0","generated_at":now()},"suggestions":suggestions})
    print(f"Roadmap items={len(roadmap)}; patch suggestions={len(suggestions)}")
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--input',default='data/updates/triaged_updates.json'); ap.add_argument('--roadmap',default='data/updates/roadmap.json'); ap.add_argument('--suggestions',default='data/updates/catalog_patch_suggestions.json'); main(ap.parse_args())
