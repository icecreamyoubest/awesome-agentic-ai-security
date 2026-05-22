from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(rel, default=''):
    p=ROOT/rel; return p.read_text(encoding='utf-8') if p.exists() else default
def build_assessment_pack(output_dir='outputs/assessment_pack'):
    outdir=ROOT/output_dir; outdir.mkdir(parents=True, exist_ok=True)
    sections=[('01_executive_summary.md','# Executive Summary\n\nAgentic Security Assessment Pack combining MCP, A2A, runtime monitoring, remediation, policy-as-code, and evidence appendix.\n'),('02_mcp_assessment.md',read('outputs/mcp_assessments/demo___local_assessment.md','# MCP Assessment\n\nRun Universal MCP Assessment to populate this section.\n')),('03_a2a_assessment.md',read('outputs/a2a_assessments/a2a_assessment.md','# A2A Assessment\n\nRun A2A assessment to populate this section.\n')),('04_runtime_monitoring.md',read('outputs/runtime_monitor/runtime_risk_timeline.md','# Runtime Monitoring\n\nRun runtime monitor to populate this section.\n')),('05_remediation_plan.md',read('outputs/remediation/remediation_plan.md','# Remediation Plan\n\nRun remediation planner to populate this section.\n')),('06_policy_bundle.md','# Policy-as-Code Bundle\n\nSee `policy_bundle/` for generated YAML/Rego policies.\n'),('07_evidence_appendix.md','# Evidence Appendix\n\nIncludes benchmark outputs, audit logs, and generated reports.\n')]
    manifest={'pack':'Agentic Security Assessment Pack','files':[]}
    for fn,content in sections: (outdir/fn).write_text(content,encoding='utf-8'); manifest['files'].append(fn)
    pb=ROOT/'outputs/policy_bundle'
    if pb.exists():
        dest=outdir/'policy_bundle'
        if dest.exists(): shutil.rmtree(dest)
        shutil.copytree(pb,dest); manifest['files'].append('policy_bundle/')
    (outdir/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); return {'output_dir':str(outdir),'manifest':manifest}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',default='outputs/assessment_pack'); args=ap.parse_args(); print(json.dumps(build_assessment_pack(args.output_dir),indent=2))
if __name__=='__main__': main()
