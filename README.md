# AI-infra-reviewer

An AI-powered Terraform code review pipeline that intercepts infrastructure PRs, runs static analysis and LLM-based reasoning, and blocks merges on critical findings via OPA policy gates.

Validated against the Terraform codebase of [ShipForge](https://github.com/Sai9700128/taskflow), a production-grade EKS platform managing 40+ AWS resources.

---

## How It Works

```
PR opened (touching .tf files)
        ↓
GitHub Actions triggers
        ↓
tflint + Checkov  →  static findings (JSON)
        ↓
Claude API  →  AI review of diff (severity-tiered JSON)
        ↓
OPA Rego policy gate  →  pass / fail
        ↓
PR comment posted with findings table
```

The static analysis layer (tflint, Checkov) runs first to filter out known-bad patterns before the AI call. Claude only sees what deterministic rules can't reason about — reducing noise and token cost.

---

## Stack

| Layer | Tool |
|---|---|
| Pipeline | GitHub Actions |
| Static analysis | tflint, Checkov |
| AI review | Claude API (claude-sonnet) |
| Policy enforcement | OPA (Rego) |
| PR feedback | GitHub API |

---

## What Gets Flagged

- **Security** — publicly accessible RDS, overly permissive IAM, missing encryption
- **Reliability** — no deletion protection on stateful resources, missing health checks
- **Cost** — redundant NAT Gateways, oversized instances for non-prod environments
- **Best practices** — missing tags, hardcoded values, no remote state backend

Findings are severity-tiered: `CRITICAL`, `HIGH`, `MEDIUM`, `INFO`.

---

## Policy Gate

OPA Rego policies consume the structured JSON output from Claude and enforce merge rules:

- `CRITICAL` → pipeline fails, merge blocked
- `HIGH` → warning posted, merge allowed
- `MEDIUM` / `INFO` → included in PR comment, no gate

Policy rules live in `policies/` as `.rego` files — auditable and reviewable independently of pipeline code.

---

## PR Comment Output

```
## 🔍 AI Infrastructure Review

| Severity | File | Line | Issue |
|----------|------|------|-------|
| 🔴 CRITICAL | rds.tf | 12 | RDS instance publicly accessible in prod |
| 🟡 HIGH | main.tf | 34 | No deletion protection on production database |
| 🔵 INFO | vpc.tf | 8 | Consider enabling VPC flow logs |

Pipeline blocked: 1 CRITICAL finding requires resolution before merge.
```

---

## Repo Structure

```
ai-infra-reviewer/
├── .github/
│   └── workflows/
│       └── review.yml        # main pipeline
├── reviewer/
│   ├── ai_review.py          # Claude API call + prompt
│   ├── policy_gate.py        # invokes OPA with findings
│   └── comment.py            # posts structured PR comment
├── policies/
│   └── review_policy.rego    # OPA Rego enforcement rules
└── README.md
```

---

## Usage in Another Repo

Call this as a reusable workflow from any repo with Terraform:

```yaml
# .github/workflows/pr.yml
jobs:
  ai-review:
    uses: Sai9700128/ai-infra-reviewer/.github/workflows/review.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Related

- [TaskFlow](https://github.com/Sai9700128/taskflow) — the EKS platform this reviewer runs against
