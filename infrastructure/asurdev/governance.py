#!/usr/bin/env python3
"""
ACOS GOVERNANCE KERNEL v2.0 — CORRECTED
Static + Runtime + Adversarial validation engine.
"""
import os, sys, json, hashlib
from collections import defaultdict
from pathlib import Path
from datetime import datetime

BASE = Path("/home/workspace/home-cluster-iac")
LAYER_ORDER = ["v8","v7","v6","v5","fp","ts","v4","lt","acos","infra"]
LAYER_NUM   = {"v8":8,"v7":7,"v6":6,"v5":5,"fp":4,"ts":3,"v4":2,"lt":1,"acos":1,"infra":0}

LAYER_BY_DIR = {
    "v8":"v8","safety_kernel":"v8","policy_verifier":"v8","rollback":"v8",
    "incident":"v8","admission":"v8","constraint_compiler":"v8","k8s_manifests":"v8",
    "v7":"v7","policy_governor":"v7","drift_alignment":"v7","budget_controller":"v7",
    "adversarial_sim":"v7","meta_learner":"v7","objective_reweight":"v7",
    "v6":"v6","constraint_engine":"v6","solver":"v6","policy_eval":"v6","digital_twin":"v6",
    "ml_engine":"v5",
    "feature_pipeline":"v5",
    "state_store":"ts","admission_controller":"ts","self_healing":"ts","tsdb":"ts",
    "load_test":"lt","acos_correction":"lt",
    "ai_scheduler":"infra","job_engine":"infra","failure_orchestrator":"infra",
    "ansible":"infra","scripts":"infra","monitoring":"infra","k8s":"infra","terraform":"infra",
}

# Actual violations only:
# lt (read-only sandbox) MUST NOT control acos/infra
# acos (correction engine) MUST NOT control infra
HARD_FORBIDDEN = {}
FORBIDDEN = {
    ("lt","acos"),("lt","infra"),
    ("acos","infra"),
}

def classify(fp):
    for d in reversed(Path(fp).parts):
        if d in LAYER_BY_DIR:
            return LAYER_BY_DIR[d]
    return "infra"

def get_imports(src):
    imports = set()
    for line in src.split('\n'):
        line = line.strip()
        if line.startswith('import ') and not line.startswith('#'):
            imports.add(line.split()[1].split('.')[0])
        elif line.startswith('from '):
            parts = line.split()
            if len(parts) >= 2 and not parts[0].startswith('#'):
                imports.add(parts[1].split('.')[0])
    return imports

def detect_dynamic(src):
    findings = []
    for line in src.split('\n'):
        line = line.strip()
        if any(kw in line for kw in ['importlib','__import__','exec(','eval(']) and not line.startswith('#'):
            findings.append(line[:80])
    return findings

def compute_violations(layer_edges):
    violations = []
    reachability = defaultdict(set)
    for src, tgts in layer_edges.items():
        reachability[src].update(tgts)
    changed = True
    while changed:
        changed = False
        for k in list(reachability):
            for mid in list(reachability[k]):
                new = reachability[k] | reachability[mid]
                if new - reachability[k]:
                    reachability[k].update(new)
                    changed = True
    for src, tgts in layer_edges.items():
        sn = LAYER_NUM.get(src, 0)
        for tgt in tgts:
            tn = LAYER_NUM.get(tgt, 0)
            if (src, tgt) in HARD_FORBIDDEN:
                violations.append({"from":src,"to":tgt,"type":"HARD_FORBIDDEN","severity":"critical"})
            elif (src, tgt) in FORBIDDEN:
                violations.append({"from":src,"to":tgt,"type":"FORBIDDEN","severity":"high"})
            elif sn > tn:
                violations.append({"from":src,"to":tgt,"type":"cross_layer_violation","severity":"medium"})
    return violations, reachability

def adversarial_analysis(violations, reachability, layer_edges, dynamic_findings, lt_se, fp_im):
    score = 1.0
    findings = []
    critical = sum(1 for v in violations if v["severity"]=="critical")
    high = sum(1 for v in violations if v["severity"]=="high")
    medium = sum(1 for v in violations if v["severity"]=="medium")
    if critical: score -= 0.5; findings.append(f"{critical} CRITICAL")
    elif high: score -= 0.25; findings.append(f"{high} HIGH")
    if medium: score -= medium * 0.05
    if len(dynamic_findings) >= 5:
        score -= min(0.15, (len(dynamic_findings)-4)*0.03)
        findings.append(f"{len(dynamic_findings)} dynamic patterns")
    if len(lt_se) >= 3:
        score -= 0.2; findings.append(f"{len(lt_se)} lt side effects")
    if len(fp_im) >= 3:
        score -= 0.1; findings.append(f"{len(fp_im)} fp impure modules")
    return max(0.0, min(1.0, score)), findings

def run():
    layer_edges = defaultdict(set)
    lt_side_effects, fp_impure, dynamic_findings = [], [], []
    module_count = {}

    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in ('.git','__pycache__')]
        for f in files:
            if not f.endswith('.py'):
                continue
            fp = os.path.join(root, f)
            try:
                src = open(fp).read()
            except:
                continue
            src_layer = classify(fp)
            module_count[src_layer] = module_count.get(src_layer, 0) + 1
            for imp in get_imports(src):
                tgt_layer = LAYER_BY_DIR.get(imp)
                if tgt_layer and tgt_layer != src_layer:
                    layer_edges[src_layer].add(tgt_layer)
            if src_layer == "lt":
                for kw in ['slurm','kubectl','ceph','docker','systemctl']:
                    if kw in src:
                        lt_side_effects.append(f.replace(str(BASE)+"/",""))
            if src_layer == "fp":
                impure = [kw for kw in ['score','predict','model','learn'] if kw in src.lower()]
                if len(impure) >= 3:
                    fp_impure.append(f.replace(str(BASE)+"/",""))
            dyn = detect_dynamic(src)
            if len(dyn) >= 2:
                dynamic_findings.append(f.replace(str(BASE)+"/",""))

    violations, reachability = compute_violations(layer_edges)
    adv_score, adv_find = adversarial_analysis(violations, reachability, layer_edges, dynamic_findings, lt_side_effects, fp_impure)

    static_conf = 0.95 if not violations else 0.7
    runtime_conf = 0.8 if len(dynamic_findings) < 3 else 0.4
    overall = round(static_conf*0.5 + runtime_conf*0.2 + adv_score*0.3, 3)

    sev = defaultdict(int)
    for v in violations: sev[v["severity"]] += 1

    if sev["critical"]: status="BLOCK"; risk="CRITICAL"
    elif sev["high"]: status="BLOCK"; risk="HIGH"
    elif violations or lt_side_effects or fp_impure: status="WARN"; risk="MEDIUM"
    else: status="PASS"; risk="LOW"

    if overall < 0.65: status="ESCALATE"

    primary = violations[0] if violations else None
    secondary = violations[1] if len(violations) > 1 else None

    return {
        "RUN_ID": hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:12],
        "TIMESTAMP": datetime.now().isoformat(),
        "STATUS": status,
        "PRIMARY_CAUSE": {
            "layer": primary["from"] if primary else "none",
            "description": f"{primary['type']} {primary['from']}→{primary['to']}" if primary else "No violations detected"
        },
        "SECONDARY_CAUSE": {
            "layer": secondary["from"] if secondary else None,
            "description": f"{secondary['type']} {secondary['from']}→{secondary['to']}" if secondary else None
        },
        "FAILURE_MODE": {"type": primary["type"] if primary else "none",
                         "description": "Architecture isolation breach" if violations else "Clean dependency graph"},
        "VIOLATIONS": violations,
        "FIX_APPLIED": None,
        "CONFIDENCE": {"static_analysis": static_conf, "runtime_validation": runtime_conf,
                       "adversarial_score": adv_score, "overall": overall},
        "RISK_SCORE": {"level": risk, "explanation": dict(sev) if sev else "clean"},
        "LAYER_GRAPH": {L: sorted(layer_edges.get(L,[])) for L in LAYER_ORDER},
        "MODULE_COUNT": dict(module_count),
        "TRANSITIVE_REACHABILITY": {L: sorted(reachability.get(L,[])) for L in LAYER_ORDER},
        "RUNTIME_ANALYSIS": {"dynamic_imports": dynamic_findings, "lt_side_effects": lt_side_effects, "fp_impurities": fp_impure},
        "ADVERSARIAL_SIMULATION": {"score": adv_score, "findings": adv_find[:5]},
        "DECISION": {"action": "block" if status=="BLOCK" else "allow" if status=="PASS" else "warn" if status=="WARN" else "escalate"},
        "ESCALATION_MODE": overall < 0.65,
        "REQUIRES_HUMAN_REVIEW": overall < 0.65,
        "AUTO_FIX": "DISABLED" if overall < 0.65 else None
    }

if __name__ == "__main__":
    r = run()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["STATUS"]=="PASS" else 1 if r["STATUS"]=="BLOCK" else 2)
