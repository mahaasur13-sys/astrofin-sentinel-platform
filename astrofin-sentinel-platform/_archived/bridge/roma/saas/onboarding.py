"""ROMA Developer Onboarding — 0-to-job in 30 seconds."""
import sys; sys.path.insert(0, '/home/workspace/roma-execution-bridge')
import logging

from auth.api_keys import APIKeyManager
from cost.predictor import CostPredictor

log = logging.getLogger(__name__)


log.info("=" * 55)
log.info("  ROMA ONBOARDING — 0-to-job in 30 seconds")
log.info("=" * 55)

# Step 1: signup → API key
akm = APIKeyManager()
org_id = "org_dev"
key = akm.create_key(org_id=org_id, project_id="default",
                     permissions=["job:submit", "job:read", "cost:estimate"])
log.info("\n[1/3] SIGNUP        org_created")
log.info(f"           org: {org_id}")
log.info(f"           key: {key[:50]}...")

# Step 2: cost preview
pred = CostPredictor().predict("train YOLOv8 on GPU", gpu_required=True, plugin_type="ml_training")
log.info("\n[2/3] COST PREVIEW shown before execution")
log.info("           task: train YOLOv8 on GPU")
log.info(f"           cost: ${pred['estimated_cost']:.4f}")
log.info(f"           gpu_seconds: {pred['breakdown']['gpu_seconds']}")
log.info(f"           decision: {pred['decision']}")

# Step 3: execute (simulate)
job_id = f"job_{org_id[:8]}_{pred['breakdown']['gpu_seconds']:.0f}"
log.info("\n[3/3] EXECUTE       job_completed")
log.info(f"           job_id: {job_id}")
log.info(f"           cost:   ${pred['estimated_cost']:.4f}")
log.info(f"           logs:   https://app.roma.sh/jobs/{job_id}/logs")

log.info(f"\n{'=' * 55}")
log.info("  First job completed (simulated 23s)")
log.info(f"  Next: roma logs {job_id}")
log.info(f"  Next: roma explain {job_id}")
log.info(f"  Next: roma scale {job_id} --replicas=3")
log.info(f"{'=' * 55}")
