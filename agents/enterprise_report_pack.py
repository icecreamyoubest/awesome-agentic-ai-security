
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
    except Exception:
        return default

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def generate_pack(scenario_path: str, output_dir: str = 'outputs/enterprise_review_pack') -> dict:
    out = ROOT / output_dir
    out.mkdir(parents=True, exist_ok=True)
    scenario = read_json(ROOT / scenario_path, {})
    validation = read_json(ROOT / 'data/validation_status.json', {"targets": []})
    benchmark = read_json(ROOT / 'validation_reports/demo_runtime_validation_report.json', {"summary": {}})
    real_mcp = read_json(ROOT / 'validation_reports/real_mcp_gateway_validation_report.json', {"summary": {}})
    llm_guard = read_json(ROOT / 'validation_reports/llm_guard_adapter_validation_report.json', {"summary": {}})
    scenario_name = scenario.get('name', 'Agentic AI Scenario')
    risks = scenario.get('risk_focus') or scenario.get('agentic_owasp') or ['ASI01','ASI02','ASI04','ASI05','ASI06','ASI07']
    def fmt_summary(rep):
        s=rep.get('summary',{})
        if not s: return 'Not run yet.'
        return f"{s.get('passed')}/{s.get('total_cases')} passed ({s.get('pass_rate',0):.0%})"
    files = {}
    exec_md = f"""# Executive Summary\n\n## Scenario\n{scenario_name}\n\n## Validation snapshot\n- Demo runtime benchmark: {fmt_summary(benchmark)}\n- Real MCP gateway smoke benchmark: {fmt_summary(real_mcp)}\n- LLM Guard adapter smoke benchmark: {fmt_summary(llm_guard)}\n\n## Key risks\n{chr(10).join('- '+r for r in risks)}\n\n## Recommendation\nUse this pack as architecture-review evidence. Treat vendor mappings as candidates until benchmark-backed or independently reviewed.\n"""
    files['executive_summary.md'] = exec_md
    arch_md = f"""# Architecture Review\n\n## Scenario\n{scenario_name}\n\n## Recommended control plane\nClient / Agent → MCP Security Gateway → Descriptor Validator → PEP/PDP → Tool Runtime → Audit Log / SIEM.\n\n## Control points\n- Validate tool descriptors before registration.\n- Enforce allowlists and typed schemas before tool execution.\n- Require HITL for high-impact actions.\n- Emit immutable audit logs for policy decisions and tool calls.\n"""
    files['architecture_review.md'] = arch_md
    asi_md = "# OWASP ASI Control Matrix\n\n| ASI | Control | Evidence |\n|---|---|---|\n" + "\n".join(f"| {r} | Map scenario risk to policy controls and benchmark tests | pending / generated |" for r in risks) + "\n"
    files['asi_control_matrix.md'] = asi_md
    bench_md = f"""# Benchmark Validation Report\n\n| Target | Result |\n|---|---:|\n| Demo Runtime | {fmt_summary(benchmark)} |\n| Real MCP Gateway | {fmt_summary(real_mcp)} |\n| LLM Guard Adapter | {fmt_summary(llm_guard)} |\n\n## Limitation\nThese reports validate included demo/adapters. Third-party tools need direct integration and independent runs.\n"""
    files['benchmark_validation_report.md'] = bench_md
    files['residual_risk_register.md'] = "# Residual Risk Register\n\n- Real MCP implementation is lightweight; production MCP requires full protocol compatibility and transport security.\n- Vendor claims remain evidence-only until benchmark-backed.\n- Human approval UX and identity integration require enterprise-specific design.\n"
    files['implementation_roadmap.md'] = "# Implementation Roadmap\n\n1. Deploy policy gate in shadow mode.\n2. Run benchmark suite against staging tools.\n3. Review evidence diffs before score updates.\n4. Integrate SIEM/OTel audit stream.\n5. Add third-party adapters for selected tools.\n"
    written=[]
    for name, text in files.items():
        p=out/name; write(p,text); written.append(str(p.relative_to(ROOT)))
    manifest={"scenario":scenario_path,"scenario_name":scenario_name,"files":written,"benchmark_summary":{"demo_runtime":benchmark.get('summary',{}),"real_mcp_gateway":real_mcp.get('summary',{}),"llm_guard_adapter":llm_guard.get('summary',{})}}
    write(out/'manifest.json', json.dumps(manifest, indent=2))
    return manifest

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--scenario', default='scenario_templates/enterprise_copilot_with_rag.json')
    ap.add_argument('--output-dir', default='outputs/enterprise_review_pack')
    args=ap.parse_args()
    print(json.dumps(generate_pack(args.scenario,args.output_dir), indent=2))
