package infra.review

import future.keywords.if
import future.keywords.in


default allow := false

allow if {
  count(critical_findings) == 0
}


critical_findings[msg] if {
  finding := input.findings[_]
  finding.severity == "CRITICAL"
  msg := sprintf("CRITICAL [%s] %s — %s", [
    finding.category,
    finding.resource,
    finding.description
  ])
}

high_findings[msg] if {
  finding := input.findings[_]
  finding.severity == "HIGH"
  msg := sprintf("HIGH [%s] %s — %s", [
    finding.category,
    finding.resource,
    finding.description
  ])
}