from __future__ import annotations
import argparse, json
from .agent_card_scanner import load_a2a_input, scan_a2a
from .trust_graph_analyzer import analyze_trust_graph
from .report_writer import write_a2a_reports

def assess_a2a(input_path_or_json: str, output_prefix: str = "outputs/a2a_assessments/a2a_assessment"):
    raw=load_a2a_input(input_path_or_json)
    report=scan_a2a(raw)
    report['trust_graph']=analyze_trust_graph(raw)
    report['summary']['mapped_asi']=sorted(set(report['summary'].get('mapped_asi', [])) | set(report['trust_graph'].get('mapped_asi', [])))
    report['report_paths']=write_a2a_reports(report, output_prefix)
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', required=True); ap.add_argument('--output-prefix', default='outputs/a2a_assessments/a2a_assessment'); args=ap.parse_args(); print(json.dumps(assess_a2a(args.input,args.output_prefix), indent=2, ensure_ascii=False))
if __name__=='__main__': main()
