#!/usr/bin/env python3
"""Monitor official sources for AI security tool, feature, incident, and roadmap updates.

The monitor is intentionally conservative: it records candidate updates and never mutates
tools.json directly. Human review remains required before catalog scores are changed.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, html, json, re, sys, urllib.request, urllib.error
from pathlib import Path
from typing import Any, Dict, List
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
KEYWORDS=["agent","guardrail","security","safety","MCP","A2A","red team","prompt injection","jailbreak","runtime","identity","OAuth","RAG","memory","roadmap","release","CVE","RCE","exfiltration"]

def load(path:str, default:Any=None):
    p=ROOT/path
    if not p.exists(): return default
    return json.loads(p.read_text(encoding='utf-8'))

def save(path:str, data:Any):
    p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')

def now(): return dt.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def digest(*parts:str)->str:
    h=hashlib.sha256()
    for p in parts: h.update((p or '').encode('utf-8','ignore'))
    return h.hexdigest()[:24]

def fetch_url(url:str, timeout:int=20)->str:
    req=urllib.request.Request(url,headers={"User-Agent":"awesome-agentic-ai-security-update-monitor/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        return resp.read().decode('utf-8','ignore')

def strip_html(text:str)->str:
    text=re.sub(r"<script[\s\S]*?</script>"," ",text,flags=re.I)
    text=re.sub(r"<style[\s\S]*?</style>"," ",text,flags=re.I)
    text=re.sub(r"<[^>]+>"," ",text)
    return re.sub(r"\s+"," ",html.unescape(text)).strip()

def extract_from_github_releases(raw:str, source:Dict[str,Any], vendor:Dict[str,Any], max_items:int)->List[Dict[str,Any]]:
    try: arr=json.loads(raw)
    except Exception: return []
    out=[]
    for item in arr[:max_items]:
        title=item.get('name') or item.get('tag_name') or 'GitHub release'
        body=strip_html(item.get('body') or '')[:1200]
        url=item.get('html_url') or source.get('url')
        published=item.get('published_at') or item.get('created_at')
        out.append(make_update(vendor,source,title,body,url,published))
    return out

def extract_from_xml(raw:str, source:Dict[str,Any], vendor:Dict[str,Any], max_items:int)->List[Dict[str,Any]]:
    out=[]
    try: root=ET.fromstring(raw)
    except Exception: return out
    for item in root.findall('.//item')[:max_items]:
        title=(item.findtext('title') or '').strip()
        desc=strip_html(item.findtext('description') or '')[:1200]
        link=(item.findtext('link') or source.get('url')).strip()
        published=(item.findtext('pubDate') or '').strip()
        out.append(make_update(vendor,source,title,desc,link,published))
    ns={'a':'http://www.w3.org/2005/Atom'}
    for item in root.findall('.//a:entry',ns)[:max_items]:
        title=(item.findtext('a:title','',ns) or '').strip()
        desc=strip_html(item.findtext('a:summary','',ns) or item.findtext('a:content','',ns) or '')[:1200]
        link=source.get('url')
        for l in item.findall('a:link',ns):
            if l.attrib.get('href'): link=l.attrib['href']; break
        published=(item.findtext('a:updated','',ns) or item.findtext('a:published','',ns) or '').strip()
        out.append(make_update(vendor,source,title,desc,link,published))
    return out

def extract_from_html(raw:str, source:Dict[str,Any], vendor:Dict[str,Any], max_items:int)->List[Dict[str,Any]]:
    text=strip_html(raw)
    # Static pages rarely provide clean feed entries. Record a single candidate when watched keywords appear.
    score=sum(1 for kw in source.get('watch_for',KEYWORDS) if kw.lower() in text.lower())
    if score==0: return []
    snippet=text[:1500]
    title=f"Watched page update candidate: {vendor.get('name')} {source.get('type')}"
    return [make_update(vendor,source,title,snippet,source.get('url'),now())]

def classify(text:str, source:Dict[str,Any])->Dict[str,Any]:
    lower=text.lower(); features=[]; asi=[]; lifecycle=[]; priority='low'
    mapping={
      'mcp':('MCP_security',['ASI02','ASI04','ASI07'],['develop_experiment','test_evaluate','deploy','operate']),
      'tool':('tool_security',['ASI02'],['develop_experiment','test_evaluate','deploy']),
      'oauth':('agent_identity',['ASI03','ASI07'],['deploy','operate','govern']),
      'identity':('agent_identity',['ASI03'],['scope_plan','deploy','govern']),
      'prompt injection':('guardrails',['ASI01','ASI02'],['test_evaluate','deploy','operate']),
      'jailbreak':('guardrails',['ASI01'],['test_evaluate','deploy','operate']),
      'rce':('code_execution_security',['ASI05'],['test_evaluate','deploy','operate']),
      'backdoor':('supply_chain',['ASI04','ASI05'],['release','deploy','operate']),
      'memory':('RAG_memory_security',['ASI06'],['augment_finetune_data','operate','monitor']),
      'rag':('RAG_memory_security',['ASI06'],['augment_finetune_data','operate','monitor']),
      'observability':('observability',['ASI08','ASI10'],['monitor','govern']),
      'roadmap':('roadmap',[],['govern']),
      'red team':('red_team',['ASI01','ASI02','ASI05'],['test_evaluate'])
    }
    for key,(feat,asis,lcs) in mapping.items():
        if key in lower:
            features.append(feat); asi+=asis; lifecycle+=lcs
    for kw in ['cve','rce','backdoor','zero-click','credential leak','exfiltration']:
        if kw in lower: priority='critical'
    if priority!='critical':
        for kw in ['prompt injection','jailbreak','mcp','tool misuse','oauth','agent']:
            if kw in lower: priority='high'
    if priority not in ['critical','high'] and any(k in lower for k in ['release','preview','roadmap','integration']): priority='medium'
    return {"features":sorted(set(features)),"asi":sorted(set(asi)),"lifecycle_stages":sorted(set(lifecycle)),"priority":priority}

def make_update(vendor,source,title,summary,url,published):
    c=classify(f"{title} {summary}",source)
    return {"id":digest(vendor.get('id',''),source.get('url',''),title,url),"vendor_id":vendor.get('id'),"vendor_name":vendor.get('name'),"source_type":source.get('type'),"source_url":source.get('url'),"title":title,"summary":summary,"url":url,"published_at":published or now(),"detected_at":now(),"matched_watch_terms":[kw for kw in source.get('watch_for',KEYWORDS) if kw.lower() in f'{title} {summary}'.lower()],"candidate_features":c['features'],"candidate_asi":c['asi'],"candidate_lifecycle_stages":c['lifecycle_stages'],"priority":c['priority'],"status":"needs_review"}

def monitor(args):
    registry=load('data/update_sources.json',{})
    seen=load('data/updates/seen_updates.json',{"seen_hashes":[]}).get('seen_hashes',[])
    updates=[]; errors=[]
    if args.offline:
        # Smoke-test update so static UI and downstream triage can be tested without network.
        v=registry.get('vendors',[{}])[0]
        s=(v.get('sources') or [{}])[0]
        updates=[make_update(v,s,'Offline smoke-test update candidate','This synthetic candidate validates the update pipeline without network access. It should not be merged as evidence.',s.get('url',''),now())]
    else:
        for vendor in registry.get('vendors',[]):
            for source in vendor.get('sources',[]):
                try:
                    raw=fetch_url(source.get('url'))
                    if source.get('type')=='github_releases': items=extract_from_github_releases(raw,source,vendor,args.max_per_source)
                    elif raw.lstrip().startswith('<rss') or raw.lstrip().startswith('<feed'): items=extract_from_xml(raw,source,vendor,args.max_per_source)
                    else: items=extract_from_html(raw,source,vendor,args.max_per_source)
                    for it in items:
                        if it['id'] not in seen and (it['matched_watch_terms'] or it['candidate_features']): updates.append(it)
                except Exception as e:
                    errors.append({"vendor":vendor.get('id'),"source":source.get('url'),"error":str(e)[:300]})
    out={"meta":{"version":"v1.0","generated_at":now(),"mode":"offline" if args.offline else "network"},"updates":updates,"errors":errors}
    save(args.output,out)
    save('data/updates/auto_update_status.json',{"meta":{"version":"v1.0","updated":now()},"last_run":now(),"mode":out['meta']['mode'],"watched_sources":sum(len(v.get('sources',[])) for v in registry.get('vendors',[])),"pending_updates":len(updates),"triaged_updates":0,"last_error":errors[:3] if errors else None,"next_steps":["Review data/updates/pending_updates.json","Run update_triage_agent.py","Open PR for accepted catalog/evidence changes"]})
    if args.update_seen:
        save('data/updates/seen_updates.json',{"seen_hashes":sorted(set(seen+[u['id'] for u in updates]))})
    print(f"Detected {len(updates)} candidate updates; errors={len(errors)}; output={args.output}")

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='data/updates/pending_updates.json')
    ap.add_argument('--max-per-source',type=int,default=5)
    ap.add_argument('--offline',action='store_true')
    ap.add_argument('--network',action='store_true')
    ap.add_argument('--update-seen',action='store_true')
    args=ap.parse_args()
    if not args.offline and not args.network:
        args.offline=True
    monitor(args)
