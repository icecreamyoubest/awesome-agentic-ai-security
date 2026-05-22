from __future__ import annotations
import argparse,json
from .trace_analyzer import analyze_trace
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--audit-log', default='examples/runtime_audit_sample.jsonl'); ap.add_argument('--output-prefix', default='outputs/runtime_monitor/runtime_risk_timeline'); args=ap.parse_args(); print(json.dumps(analyze_trace(args.audit_log,args.output_prefix), indent=2))
if __name__=='__main__': main()
