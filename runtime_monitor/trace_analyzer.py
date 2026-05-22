from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from .anomaly_detector import detect_anomalies

def read_jsonl(path: str) -> List[Dict[str, Any]]:
    p=Path(path); events=[]
    if not p.exists(): return []
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        try: events.append(json.loads(line))
        except Exception: pass
    return events
def analyze_trace(path: str, output_prefix='outputs/runtime_monitor/runtime_risk_timeline'):
    events=read_jsonl(path); findings=detect_anomalies(events); mapped=sorted({asi for f in findings for asi in f.get('mapped_asi',[])})
    report={'assessment_type':'runtime_monitoring_simulation','events':len(events),'findings':findings,'mapped_asi':mapped,'summary':{'risk_events':len(findings),'risk_level':'high' if any(f.get('severity')=='high' for f in findings) else ('medium' if findings else 'low')}}
    prefix=Path(output_prefix); prefix.parent.mkdir(parents=True, exist_ok=True); prefix.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['# Runtime Risk Timeline','',f"Events analyzed: `{len(events)}`",f"Risk events: `{len(findings)}`",''] + [f"- **{f.get('severity')}** `{f.get('type')}` tool={f.get('tool')} ASI={', '.join(f.get('mapped_asi', []))}" for f in findings]
    prefix.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); report['report_paths']={'json':str(prefix.with_suffix('.json')),'markdown':str(prefix.with_suffix('.md'))}; return report
