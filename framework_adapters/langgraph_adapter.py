from __future__ import annotations
import json
from pathlib import Path

def load_graph(path_or_json: str):
    p=Path(path_or_json)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else json.loads(path_or_json)
def assess_langgraph_config(config):
    nodes=config.get('nodes',[]); tools=config.get('tools',[]) or config.get('mcp_tools',[]); memory=config.get('memory') or config.get('retriever'); external=config.get('external_apis',[]); mapped=[]; signals=[]
    if tools: mapped += ['ASI02','ASI04']; signals.append('tool_use')
    if any('mcp' in str(t).lower() for t in tools): mapped += ['ASI02','ASI04','ASI07']; signals.append('mcp_tools')
    if memory: mapped += ['ASI06']; signals.append('memory_or_rag')
    if external: mapped += ['ASI03','ASI07']; signals.append('external_api')
    if len(nodes)>3: mapped += ['ASI08']; signals.append('multi_step_graph')
    return {'framework':'langgraph','nodes':len(nodes),'tools':len(tools),'signals':signals,'mapped_asi':sorted(set(mapped)),'recommended_benchmarks':['MCPV2-ASI02-001','MCPV2-ASI04-002']+(['RAG-ASI06-001'] if memory else []),'recommended_controls':['tool-call PEP/PDP','graph-level audit trace','memory provenance','human approval for high-impact tools']}
def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',required=True); ap.add_argument('--output',default='outputs/framework_adapters/langgraph_assessment.json'); args=ap.parse_args(); report=assess_langgraph_config(load_graph(args.graph)); p=Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
