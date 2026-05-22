package agentic.tool_policy

default allow := false

allow if {
  input.tool in data.allowed_tools
  not high_impact_without_approval
}

high_impact_without_approval if {
  input.tool in data.high_impact_tools
  not input.human_approved
}
