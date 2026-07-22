
import logging

log = logging.getLogger(__name__)

"""ROMA SaaS Onboarding Pipeline — 5-min signup flow."""
log.info("=== ROMA SaaS Onboarding Pipeline ===")
log.info("Step 1: org.create('acme')")
log.info("Step 2: api_key = org.provision_api_key()")
log.info("Step 3: roma.run('task', api_key=api_key)")
log.info("→ Dashboard at https://app.roma.sh/org/acme")
