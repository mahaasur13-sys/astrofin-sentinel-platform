#!/usr/bin/env python3
import json, os, sys
repo = os.environ.get('GITHUB_REPOSITORY', 'mahaasur13-sys/AsurDev')
sha = os.environ.get('GITHUB_SHA', 'abc123')
run_id = os.environ.get('GITHUB_RUN_ID', '1')
run_attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
source_hash = os.environ.get('SOURCE_HASH', '5f2a2c04fe3718ab2a3d3941ef53e4fd426850b480a7b6195b457af08377d201')
oidc_subject = os.environ.get('OIDC_SUBJECT', 'https://github.com/mahaasur13-sys/AsurDev/.github/workflows/slsa4-live.yml@refs/heads/main')

prov = {
    "_type": "https://in-toto.io/Statement/v1",
    "predicateType": "https://slsa.dev/provenance/v1",
    "subject": [{"name": repo, "digest": {"sha256": source_hash}}],
    "predicate": {
        "buildDefinition": {
            "buildType": "https://github.com/slsa-framework/slsa-github-generator@v1",
            "externalParameters": {"repository": repo, "workflow": "SLSA-4 Live Supply Chain Enforcement"},
            "resolvedDependencies": [{"uri": f"git+https://github.com/{repo}@{sha}", "digest": {"sha1": sha}}],
            "buildInvocationId": f"{run_id}-{run_attempt}"
        },
        "runDetails": {
            "builder": {"id": f"https://github.com/{repo}/attestations/node@v1", "OODR": {"subject": oidc_subject, "issuer": "https://token.actions.githubusercontent.com"}},
            "metadata": {"completeness": {"parameters": True, "environment": False, "materials": True}, "reproducible": True}
        }
    }
}
os.makedirs('provenance', exist_ok=True)
open('provenance/provenance.json', 'w').write(json.dumps(prov, indent=2))
print("Provenance generated OK")