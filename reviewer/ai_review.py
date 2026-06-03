import json
import os
import sys
import urllib.request
import urllib.error

def read_diff():
    """Read the terraform diff file"""
    try:
        with open('tf.diff', 'r') as f:
            diff = f.read().strip()
        if not diff:
            print("No diff found — nothing to review")
            sys.exit(0)
        return diff
    except FileNotFoundError:
        print("tf.diff not found")
        sys.exit(1)

def call_claude(diff: str) -> dict:
    """Send diff to Claude API and get structured findings"""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    prompt = f"""You are an expert infrastructure security and reliability engineer reviewing a Terraform pull request.

Analyze the following Terraform diff and identify issues across these categories:
- SECURITY: exposed resources, missing encryption, overly permissive IAM, hardcoded secrets
- RELIABILITY: no deletion protection, missing health checks, single points of failure
- COST: oversized instances, redundant resources, inefficient configurations
- BEST_PRACTICE: missing tags, hardcoded values, naming conventions, missing remote state

For each issue found, assign a severity:
- CRITICAL: must fix before merge (e.g. publicly accessible production database)
- HIGH: should fix soon (e.g. no deletion protection on stateful resource)
- MEDIUM: worth fixing (e.g. missing tags)
- INFO: suggestion (e.g. consider enabling a feature)

Respond ONLY with a valid JSON object in exactly this format, no preamble, no markdown:
{{
  "findings": [
    {{
      "severity": "CRITICAL",
      "category": "SECURITY",
      "line": 12,
      "resource": "aws_db_instance.prod",
      "description": "RDS instance is publicly accessible",
      "suggestion": "Set publicly_accessible = false for production databases"
    }}
  ],
  "summary": "Brief one sentence summary of the overall review"
}}

If no issues are found, return: {{"findings": [], "summary": "No issues found in this diff"}}

Terraform diff to review:
{diff}"""

    payload = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            raw_text = data['content'][0]['text']
            return json.loads(raw_text)
    except urllib.error.HTTPError as e:
        print(f"Claude API error: {e.code} {e.read().decode()}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Failed to parse Claude response as JSON: {e}")
        sys.exit(1)

def main():
    print("Reading Terraform diff...")
    diff = read_diff()
    print(f"Diff is {len(diff)} characters — sending to Claude...")

    results = call_claude(diff)

    findings = results.get('findings', [])
    summary = results.get('summary', '')

    print(f"Claude returned {len(findings)} findings")
    print(f"Summary: {summary}")

    with open('ai_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("Saved to ai_results.json")

if __name__ == '__main__':
    main()