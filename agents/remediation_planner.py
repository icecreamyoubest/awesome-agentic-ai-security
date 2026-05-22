from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any, Dict, List
ROOT=Path(__file__).resolve().parents[1]
def load_json(path: Path, default=None):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return default
def collect_asi(obj: Any) -> List[str]:
    found=set()
    def walk(x):
        if isinstance(x, dict):
            for k,v in x.items():
                if k in {'mapped_asi','asi','owasp_asi'}:
                    vals=v if isinstance(v,list) else [v]
                    for item in vals:
                        if isinstance(item,str) and item.startswith('ASI'): found.add(item[:5])
                walk(v)
        elif isinstance(x, list):
            for i in x: walk(i)
        elif isinstance(x, str) and x.startswith('ASI'): found.add(x[:5])
    walk(obj); return sorted(found)
def build_remediation(input_report: Dict[str, Any], output_prefix='outputs/remediation/remediation_plan'):
    patterns=load_json(ROOT/'data/remediation_patterns.json',{}) or {}; asis=collect_asi(input_report) or ['ASI02','ASI04','ASI07']; items=[]
    for asi in asis:
        p=patterns.get(asi,{})
        items.append({'asi':asi,'risk':p.get('risk','Unknown'),'recommended_controls':p.get('controls',[]),'validation_benchmarks':p.get('benchmarks',[]),'implementation_notes':['Place PEP/PDP before tool or agent action execution.','Record policy decision, subject, tool/action, arguments, and outcome in immutable audit logs.','Treat generated model/tool output as untrusted until validated.']})
    out={'assessment_type':'remediation_plan','mapped_asi':asis,'items':items}; prefix=ROOT/output_prefix; prefix.parent.mkdir(parents=True, exist_ok=True); prefix.with_suffix('.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# Remediation Plan','',f"Mapped ASI: {', '.join(asis)}",'']
    for it in items:
        lines += [f"## {it['asi']} — {it['risk']}",'','### Controls'] + [f"- {c}" for c in it['recommended_controls']] + ['','### Validation'] + [f"- Run `{b}`" for b in it['validation_benchmarks']] + ['']
    prefix.with_suffix('.md').write_text('\n'.join(lines),encoding='utf-8'); out['report_paths']={'json':str(prefix.with_suffix('.json')),'markdown':str(prefix.with_suffix('.md'))}; return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-report', required=True); ap.add_argument('--output-prefix', default='outputs/remediation/remediation_plan'); args=ap.parse_args(); print(json.dumps(build_remediation(load_json(Path(args.input_report),{}) or {}, args.output_prefix), indent=2, ensure_ascii=False))
if __name__=='__main__': main()
