package infra.review

# default: deny
default allow = false

# allow only if no critical findings
allow {
  count(critical_findings) == 0
}

# collect critical findings
critical_findings[msg] {
  finding := input.findings[_]
  finding.severity == "CRITICAL"
  msg := sprintf("CRITICAL [%s] %s - %s", [finding.category, finding.resource, finding.description])
}

# collect high findings
high_findings[msg] {
  finding := input.findings[_]
  finding.severity == "HIGH"
  msg := sprintf("HIGH [%s] %s - %s", [finding.category, finding.resource, finding.description])
}

# summary object
summary = {
  "allow": allow,
  "critical_count": count(critical_findings),
  "high_count": count(high_findings),
  "critical_findings": critical_findings,
  "high_findings": high_findings
}

