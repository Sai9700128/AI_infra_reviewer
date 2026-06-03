Downloads the OPA binary into the Github Actions runner , OPA isn't pre-installed so we fetch it at runtime.

def install_opa():
    opa_url = "https://openpolicyagent.org/downloads/v0.68.0/opa_linux_amd64_static"
    urllib.request.urlretrieve(opa_url, "/usr/local/bin/opa")
    os.chmod("/usr/local/bin/opa", 0o755)

Reads Claude's output from the previos step. This is what gets passed to OPA as input.

def load_findings():
    with open('ai_results.json', 'r') as f:
        return json.load(f)

# OPA RUN

def run_opa(findings: dict) -> dict:
    with open('opa_input.json', 'w') as f:
        json.dump(findings, f)

    result = subprocess.run([
        "opa", "eval",
        "--input", "opa_input.json",
        "--data", "policies/review_policy.rego",
        "--format", "json",
        "data.infra.review.summary"
    ], capture_output=True, text=True)

    opa_output = json.loads(result.stdout)
    return opa_output['result'][0]['expressions'][0]['value']


if not summary['allow']:
    print(f"❌ Pipeline FAILED — {summary['critical_count']} CRITICAL finding(s)")
    sys.exit(1)   # ← this is what blocks the merge
else:
    print(f"✅ Pipeline PASSED — no critical findings")
    sys.exit(0)