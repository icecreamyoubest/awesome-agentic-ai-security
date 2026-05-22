# v1.9.1 Interactive Visualization Dashboard

This release adds an interactive visual analytics layer for the real multi-agent refund workflow demo.

## What it visualizes

- Multi-agent network graph: agents, tools, policy engine, audit sink, and blocked edges
- Execution timeline replay: step-by-step flow and attack containment events
- Tool-call audit explorer: decision, reason, mapped OWASP ASI, controls, and trace ID
- ASI risk coverage dashboard: evidence-linked coverage counts
- A2A trust / delegation graph data: signed trust edges and blocked forged delegation

## WebUI

Run:

```bash
pip install -r requirements.txt
python app.py
```

Open the Gradio UI and use:

```text
14. Interactive Visualization
```

Click **Run demo and build interactive visualization**.

## Generated files

```text
outputs/visualizations/
├── interactive_dashboard.html
├── visualization_bundle.json
├── graph_nodes.json
├── graph_edges.json
├── timeline_events.json
├── audit_table.json
├── risk_dashboard.json
└── trust_graph.json
```

## Security interpretation

This dashboard visualizes evidence produced by the deterministic local demo runtime. It is intended to show explainable security controls for an agentic workflow, not to claim validation of third-party commercial tools.
