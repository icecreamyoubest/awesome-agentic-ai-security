from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_json(path: Path, default=None):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return default
def to_yaml(obj, indent=0):
    sp='  '*indent
    if isinstance(obj, dict):
        lines=[]
        for k,v in obj.items():
            if isinstance(v,(dict,list)): lines.append(f'{sp}{k}:'); lines.append(to_yaml(v, indent+1))
            else: lines.append(f"{sp}{k}: {json.dumps(v) if isinstance(v,str) else str(v).lower() if isinstance(v,bool) else v}")
        return '\n'.join(lines)
    if isinstance(obj, list): return '\n'.join(f"{sp}- {json.dumps(x) if isinstance(x,str) else x}" for x in obj)
    return f'{sp}{obj}'
def generate_policy_bundle(remediation_report, output_dir='outputs/policy_bundle'):
    outdir=ROOT/output_dir; outdir.mkdir(parents=True, exist_ok=True); high_tools=['email.send','crm.refund','file.delete','package.install','shell.run']
    policy={'tool_policies': {'default': {'deny_unknown_tools': True, 'audit_required': True, 'require_schema_validation': True}, 'high_impact_tools': {'tools': high_tools, 'require_human_approval': True, 'scoped_token_ttl_seconds': 300}, 'egress': {'default':'deny','allowlisted_domains':['company.com']}}, 'identity_scope_policy': {'per_agent_identity': True, 'short_lived_tokens': True, 'deny_privilege_inheritance': True}, 'mapped_asi': remediation_report.get('mapped_asi', [])}
    yaml_text=to_yaml(policy); (outdir/'mcp_tool_policy.yaml').write_text(yaml_text,encoding='utf-8'); rego=(ROOT/'policy_templates/opa_tool_policy.rego').read_text(encoding='utf-8'); (outdir/'opa_tool_policy.rego').write_text(rego,encoding='utf-8'); manifest={'bundle':'agentic_policy_bundle','files':['mcp_tool_policy.yaml','opa_tool_policy.rego'],'mapped_asi':policy['mapped_asi']}; (outdir/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); return {'manifest':manifest,'output_dir':str(outdir),'yaml':yaml_text}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--remediation-report', default='outputs/remediation/remediation_plan.json'); ap.add_argument('--output-dir', default='outputs/policy_bundle'); args=ap.parse_args(); print(json.dumps(generate_policy_bundle(load_json(ROOT/args.remediation_report, {'mapped_asi':['ASI02','ASI03','ASI07']}) or {}, args.output_dir), indent=2, ensure_ascii=False))
if __name__=='__main__': main()
