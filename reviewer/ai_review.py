import json
import os
import sys
import urllib.request
import urllib.error

def read_diff():
    try:
        with open('tf.diff', 'r') as f:
            diff = f.read().strip()
        if not diff:
            print("No diff found — nothing to review")
            # write empty results so the comment step doesn't fail
            with open('ai_results.json', 'w') as f:
                json.dump({"findings": [], "summary": "No Terraform changes detected"}, f)
            sys.exit(0)
        return diff
    except FileNotFoundError:
        print("tf.diff not found")
        sys.exit(1)

def extract_json(text: str) -> dict:
    """Try multiple strategies to extract JSON from Claude's response"""
    text = text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown code fences
    if '```' in text:
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

    # Strategy 3: find the first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    # Fallback
    print(f"Could not parse JSON from response:\n{text[:500]}")
    return {"findings": [], "summary": "AI review could not be parsed"}

def call_claude(diff: str) -> dict:
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    prompt = f"""You are an expert infrastructure security and reliability engineer reviewing a Terraform pull request.

Analyze the following Terraform diff and identify issues across these categories:
- SECURITY: exposed resources, missing encryption, overly permissive IAM, hardcoded secrets
- RELIABILITY: no deletion protection, missing health checks, single points of failure
- COST: oversized instances, redundant resources, inefficient configurations
- BEST_PRACTICE: missing tags, hardcoded values, naming conventions

For each issue found, assign a severity:
- CRITICAL: must fix before merge (e.g. publicly accessible production database)
- HIGH: should fix soon (e.g. no deletion protection on stateful resource)
- MEDIUM: worth fixing (e.g. missing tags)
- INFO: suggestion only

YOU MUST RESPOND WITH ONLY A JSON OBJECT. NO TEXT BEFORE OR AFTER. NO MARKDOWN. NO EXPLANATION.

Required format:
{{"findings": [{{"severity": "CRITICAL", "category": "SECURITY", "line": 12, "resource": "aws_db_instance.prod", "description": "RDS instance is publicly accessible", "suggestion": "Set publicly_accessible = false"}}], "summary": "One sentence summary"}}

If no issues found: {{"findings": [], "summary": "No issues found in this diff"}}

Terraform diff:
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
            print(f"Claude raw response:\n{raw_text[:500]}")
            return extract_json(raw_text)
    except urllib.error.HTTPError as e:
        print(f"Claude API error: {e.code} {e.read().decode()}")
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