import json
import os
import sys
import subprocess
import urllib.request

def install_opa():
    """Download and install OPA binary"""
    print("Installing OPA...")
    opa_url = "https://openpolicyagent.org/downloads/v0.68.0/opa_linux_amd64_static"
    urllib.request.urlretrieve(opa_url, "/usr/local/bin/opa")
    os.chmod("/usr/local/bin/opa", 0o755)
    print("OPA installed successfully")

def load_findings():
    """Load Claude findings from ai_results.json"""
    try:
        with open('ai_results.json', 'r') as f:
            data = json.load(f)
            print(f"Loaded {len(data.get('findings', []))} findings")
            return data
    except FileNotFoundError:
        print("ai_results.json not found - skipping policy gate")
        sys.exit(0)

def run_opa(findings):
    """Run OPA policy evaluation against findings"""
    # write findings to input file
    with open('opa_input.json', 'w') as f:
        json.dump(findings, f)
    print("Running OPA evaluation...")

    # new — reads from env var, falls back to default
policy_path = os.environ.get('POLICY_PATH', 'policies/review_policy.rego')


    result = subprocess.run(
        [
            "opa", "eval",
            "--input", "opa_input.json",
            "--data", policy_path,
            "--format", "json",
            "data.infra.review.summary"
        ],
        capture_output=True,
        text=True
    )

    print(f"OPA stdout: {result.stdout[:500]}")
    print(f"OPA stderr: {result.stderr[:500]}")

    if result.returncode != 0:
        print(f"OPA failed with return code {result.returncode}")
        sys.exit(1)

    try:
        opa_output = json.loads(result.stdout)
        summary = opa_output['result'][0]['expressions'][0]['value']
        return summary
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Failed to parse OPA output: {e}")
        print(f"Raw output: {result.stdout}")
        sys.exit(1)

def main():
    install_opa()

    print("Loading findings...")
    findings = load_findings()

    print("Running OPA policy evaluation...")
    summary = run_opa(findings)

    print(f"\n{'='*40}")
    print(f"Policy Gate Result")
    print(f"{'='*40}")
    print(f"Allow merge:       {summary.get('allow')}")
    print(f"Critical findings: {summary.get('critical_count')}")
    print(f"High findings:     {summary.get('high_count')}")

    if summary.get('critical_findings'):
        print(f"\nBlocking issues:")
        for msg in summary['critical_findings']:
            print(f"  CRITICAL: {msg}")

    if summary.get('high_findings'):
        print(f"\nWarnings:")
        for msg in summary['high_findings']:
            print(f"  HIGH: {msg}")

    # save result for PR comment step
    with open('policy_result.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("Saved policy_result.json")

    print(f"{'='*40}")

    # exit 1 blocks the merge
    if not summary.get('allow'):
        print(f"\nPipeline FAILED - {summary.get('critical_count', 0)} CRITICAL finding(s) must be resolved")
        sys.exit(1)
    else:
        print(f"\nPipeline PASSED - no critical findings")
        sys.exit(0)

if __name__ == '__main__':
    main()