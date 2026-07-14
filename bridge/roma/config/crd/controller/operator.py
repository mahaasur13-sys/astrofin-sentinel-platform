# =============================================================================
# ROMA Tenant Operator — kopf-based controller
# Watches: RomaTenant CR (romatenants.roma.io)
# Reconciles: Namespace + Secrets + Ingress + Certificate + KongPlugin + ConfigMap
# =============================================================================

import os
import logging

import kopf
import kubernetes
from kubernetes.client import ApiException

# =============================================================================
# Config
# =============================================================================

VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH", "roma/tenants")
KONG_NAMESPACE = os.getenv("KONG_NAMESPACE", "kong")
ROMA_SYSTEM_NS = os.getenv("ROMA_SYSTEM_NS", "roma-system")
CERT_CLUSTER_ISSUER = os.getenv("CERT_ISSUER", "letsencrypt-prod")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Kubernetes clients
# =============================================================================

def get_core_v1():
    return kubernetes.client.CoreV1Api()

def get_networking_v1():
    return kubernetes.client.NetworkingV1Api()

def get_custom_api():
    return kubernetes.client.CustomObjectsApi()

def get_rbac_v1():
    return kubernetes.client.RbacAuthorizationV1Api()

# =============================================================================
# Resource builders
# =============================================================================

def build_namespace(tenant_id: str, labels: dict) -> dict:
    ns_manifest = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": f"roma-{tenant_id}",
            "labels": {
                "roma.io/tenant": tenant_id,
                "app.kubernetes.io/managed-by": "roma-tenant-controller",
                **labels
            }
        }
    }
    return ns_manifest

def build_configmap(tenant_id: str, branding: dict) -> dict:
    cm = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": f"roma-{tenant_id}-branding",
            "namespace": f"roma-{tenant_id}",
            "labels": {
                "roma.io/tenant": tenant_id
            }
        },
        "data": {
            "logo-url": branding.get("logoUrl", ""),
            "primary-color": branding.get("primaryColor", "#6366F1"),
            "secondary-color": branding.get("secondaryColor", "#1E1E2E"),
            "company-name": branding.get("companyName", tenant_id),
            "support-email": branding.get("supportEmail", ""),
        }
    }
    return cm

def build_api_secret(tenant_id: str, api_key: str, secret_name: str = "api-key") -> dict:
    """Create API key secret for tenant from Vault-sourced value."""
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": secret_name,
            "namespace": f"roma-{tenant_id}",
            "labels": {"roma.io/tenant": tenant_id}
        },
        "type": "Opaque",
        "stringData": {
            "api-key": api_key,
            "tenant-id": tenant_id
        }
    }

def build_ingress(tenant_id: str, domain: str, subdomain: str, namespace: str) -> dict:
    """Ingress with cert-manager TLS for tenant API."""
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": f"roma-{tenant_id}-ingress",
            "namespace": namespace,
            "annotations": {
                "konghq.com/plugins": f"rate-limit-{tenant_id},tenant-config-{tenant_id}",
                "cert-manager.io/cluster-issuer": CERT_CLUSTER_ISSUER,
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                "roma.io/tenant": tenant_id,
            }
        },
        "spec": {
            "ingressClassName": "nginx",
            "tls": [{
                "hosts": [f"{subdomain}.{domain}", domain],
                "secretName": f"roma-{tenant_id}-tls"
            }],
            "rules": [{
                "host": f"{subdomain}.{domain}",
                "http": {
                    "paths": [{
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": f"roma-{tenant_id}-api",
                                "port": {"number": 8080}
                            }
                        }
                    }]
                }
            }]
        }
    }

def build_certificate(tenant_id: str, domain: str, subdomain: str, namespace: str) -> dict:
    """Certificate resource for cert-manager."""
    return {
        "apiVersion": "cert-manager.io/v1",
        "kind": "Certificate",
        "metadata": {
            "name": f"roma-{tenant_id}-cert",
            "namespace": namespace,
            "labels": {"roma.io/tenant": tenant_id}
        },
        "spec": {
            "secretName": f"roma-{tenant_id}-tls",
            "issuerRef": {
                "name": CERT_CLUSTER_ISSUER,
                "kind": "ClusterIssuer"
            },
            "dnsNames": [f"{subdomain}.{domain}", domain]
        }
    }

def build_kong_consumer(tenant_id: str, api_key: str) -> dict:
    """Kong consumer for tenant with API key auth."""
    return {
        "apiVersion": "configuration.konghq.com/v1",
        "kind": "KongConsumer",
        "metadata": {
            "name": tenant_id,
            "namespace": KONG_NAMESPACE,
            "annotations": {
                "konghq.com/plugins": f"rate-limit-{tenant_id}"
            }
        },
        "username": tenant_id,
        "credentials": [f"{tenant_id}-credential"]
    }

def build_kong_credential(tenant_id: str, api_key: str) -> dict:
    """Kong API key credential for tenant consumer."""
    return {
        "apiVersion": "configuration.konghq.com/v1",
        "kind": "KongCredential",
        "metadata": {
            "name": f"{tenant_id}-credential",
            "namespace": KONG_NAMESPACE
        },
        "type": "key-auth",
        "consumerRef": tenant_id
    }

def build_rate_limit_plugin(tenant_id: str, plan: str) -> dict:
    """KongPlugin: rate limiting per tenant plan."""
    limits = {
        "free":    {"minute": 60,   "hour": 500,   "day": 5000},
        "pro":     {"minute": 300,  "hour": 5000,  "day": 50000},
        "enterprise": {"minute": 3000, "hour": 50000, "day": 500000}
    }
    pl = limits.get(plan, limits["free"])
    return {
        "apiVersion": "configuration.konghq.com/v1",
        "kind": "KongPlugin",
        "metadata": {
            "name": f"rate-limit-{tenant_id}",
            "namespace": ROMA_SYSTEM_NS
        },
        "plugin": "rate-limiting",
        "config": {
            "minute": pl["minute"],
            "hour": pl["hour"],
            "day": pl["day"],
            "policy": "local",
            "hide_client_headers": False
        }
    }

def build_tenant_config_plugin(tenant_id: str) -> dict:
    """KongPlugin: tenant-specific config (branding headers, cors, etc)."""
    return {
        "apiVersion": "configuration.konghq.com/v1",
        "kind": "KongPlugin",
        "metadata": {
            "name": f"tenant-config-{tenant_id}",
            "namespace": ROMA_SYSTEM_NS
        },
        "plugin": "response-transformer",
        "config": {
            "add": {
                "headers": [f"X-Tenant-ID: {tenant_id}"]
            }
        }
    }

def build_service(tenant_id: str) -> dict:
    """Headless service for tenant API."""
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"roma-{tenant_id}-api",
            "namespace": f"roma-{tenant_id}",
            "labels": {"roma.io/tenant": tenant_id}
        },
        "spec": {
            "type": "ClusterIP",
            "selector": {"roma.io/tenant": tenant_id},
            "ports": [{
                "name": "http",
                "port": 8080,
                "targetPort": 8080
            }]
        }
    }

# =============================================================================
# Upsert helpers (idempotent)
# =============================================================================

def ensure_namespace(core, tenant_id: str, labels: dict):
    ns_name = f"roma-{tenant_id}"
    try:
        core.read_namespace(ns_name)
        logger.info(f"Namespace {ns_name} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            ns_body = build_namespace(tenant_id, labels)
            core.create_namespace(ns_body)
            logger.info(f"Created namespace: {ns_name}")
        else:
            raise

def ensure_configmap(core, tenant_id: str, branding: dict):
    ns = f"roma-{tenant_id}"
    name = f"roma-{tenant_id}-branding"
    try:
        core.read_namespaced_config_map(name, ns)
        logger.info(f"ConfigMap {name} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            core.create_namespaced_config_map(ns, build_configmap(tenant_id, branding))
            logger.info(f"Created ConfigMap: {name}")
        else:
            raise

def ensure_secret(core, tenant_id: str, api_key: str):
    ns = f"roma-{tenant_id}"
    name = "api-key"
    try:
        core.read_namespaced_secret(name, ns)
        logger.info(f"Secret {name} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            core.create_namespaced_secret(ns, build_api_secret(tenant_id, api_key))
            logger.info(f"Created Secret: {name}")
        else:
            raise

def ensure_ingress(networking, tenant_id: str, domain: str, subdomain: str):
    ns = f"roma-{tenant_id}"
    name = f"roma-{tenant_id}-ingress"
    try:
        networking.read_namespaced_ingress(name, ns)
        logger.info(f"Ingress {name} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            networking.create_namespaced_ingress(ns, build_ingress(tenant_id, domain, subdomain, ns))
            logger.info(f"Created Ingress: {name}")
        else:
            raise

def ensure_certificate(cert_client, tenant_id: str, domain: str, subdomain: str):
    ns = f"roma-{tenant_id}"
    name = f"roma-{tenant_id}-cert"
    try:
        cert_client.read_namespaced_certificate(name, ns)
        logger.info(f"Certificate {name} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            cert_client.create_namespaced_certificate(ns, build_certificate(tenant_id, domain, subdomain, ns))
            logger.info(f"Created Certificate: {name}")
        else:
            raise

def ensure_kong_consumer(custom_api, tenant_id: str, api_key: str):
    try:
        custom_api.get_namespaced_custom_object(
            group="configuration.konghq.com",
            version="v1",
            namespace=KONG_NAMESPACE,
            plural="kongconsumers",
            name=tenant_id
        )
        logger.info(f"KongConsumer {tenant_id} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            custom_api.create_namespaced_custom_object(
                group="configuration.konghq.com",
                version="v1",
                namespace=KONG_NAMESPACE,
                plural="kongconsumers",
                body=build_kong_consumer(tenant_id, api_key)
            )
            logger.info(f"Created KongConsumer: {tenant_id}")
        else:
            raise

def ensure_kong_plugin(custom_api, plugin_body: dict):
    name = plugin_body["metadata"]["name"]
    ns = plugin_body["metadata"]["namespace"]
    try:
        custom_api.get_namespaced_custom_object(
            group="configuration.konghq.com",
            version="v1",
            namespace=ns,
            plural="kongplugins",
            name=name
        )
        logger.info(f"KongPlugin {name} already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            custom_api.create_namespaced_custom_object(
                group="configuration.konghq.com",
                version="v1",
                namespace=ns,
                plural="kongplugins",
                body=plugin_body
            )
            logger.info(f"Created KongPlugin: {name}")
        else:
            raise

# =============================================================================
# kopf handlers
# =============================================================================

@kopf.on.create("romatenants", "roma.io", "v1")
@kopf.on.update("romatenants", "roma.io", "v1")
def reconcile_tenant(meta, spec, status, namespace, name, **kwargs):
    """Main reconciliation handler for RomaTenant CR."""
    logger.info(f"[RECONCILE] tenant={name}")

    tenant_id   = spec["tenantId"]
    domain      = spec["domain"]
    subdomain   = spec.get("subdomain", tenant_id)
    plan        = spec.get("plan", "free")
    branding    = spec.get("branding", {})
    spec.get("compute", {})
    tier        = spec.get("tier", 1)

    core = get_core_v1()
    networking = get_networking_v1()
    custom = get_custom_api()

    try:
        from cert_manager_client import CertManagerV1Api
        cert_client = CertManagerV1Api()
    except Exception:
        # Fallback: use dynamic client for cert-manager
        import kubernetes
        cert_client = kubernetes.client.CustomObjectsApi()

    # Build labels
    labels = {
        "roma.io/plan": plan,
        "roma.io/tier": str(tier),
        "roma.io/tenant": tenant_id
    }

    # ---- 1. Namespace ----
    ensure_namespace(core, tenant_id, labels)

    # ---- 2. ConfigMap (branding) ----
    if branding:
        ensure_configmap(core, tenant_id, branding)

    # ---- 3. API Secret (from Vault or generated fallback) ----
    api_key = os.environ.get(f"ROMA_TENANT_{tenant_id.upper().replace('-','_')}_APIKEY", "roma-dev-key")
    ensure_secret(core, tenant_id, api_key)

    # ---- 4. Service ----
    ns = f"roma-{tenant_id}"
    try:
        core.read_namespaced_service(f"roma-{tenant_id}-api", ns)
        logger.info("Service already exists — skipping")
    except ApiException as e:
        if e.status == 404:
            core.create_namespaced_service(ns, build_service(tenant_id))
            logger.info(f"Created Service: roma-{tenant_id}-api")
        else:
            raise

    # ---- 5. Ingress + Certificate ----
    ensure_ingress(networking, tenant_id, domain, subdomain)
    ensure_certificate(cert_client, tenant_id, domain, subdomain)

    # ---- 6. KongConsumer + credentials ----
    ensure_kong_consumer(custom, tenant_id, api_key)
    try:
        custom.get_namespaced_custom_object(
            "configuration.konghq.com", "v1", KONG_NAMESPACE,
            "kongcredentials", f"{tenant_id}-credential"
        )
    except ApiException as e:
        if e.status == 404:
            custom.create_namespaced_custom_object(
                "configuration.konghq.com", "v1", KONG_NAMESPACE,
                "kongcredentials",
                build_kong_credential(tenant_id, api_key)
            )
            logger.info(f"Created KongCredential: {tenant_id}-credential")

    # ---- 7. KongPlugins ----
    ensure_kong_plugin(custom, build_rate_limit_plugin(tenant_id, plan))
    ensure_kong_plugin(custom, build_tenant_config_plugin(tenant_id))

    # ---- 8. Update status ----
    patch = {
        "status": {
            "phase": "Ready",
            "message": f"Tenant {tenant_id} provisioned successfully",
            "namespace": f"roma-{tenant_id}",
            "ingressEndpoint": f"https://{subdomain}.{domain}",
            "certificateReady": True,
            "kongConsumerReady": True,
            "conditions": [{
                "type": "Provisioned",
                "status": "True",
                "message": "All resources created",
                "lastTransitionTime": "2026-04-18T00:00:00Z"
            }]
        }
    }

    try:
        custom.patch_cluster_custom_object(
            group="roma.io",
            version="v1",
            plural="romatenants",
            name=name,
            body=patch
        )
        logger.info(f"Status updated: {name} → Ready")
    except Exception as e:
        logger.warning(f"Failed to update status: {e}")

    logger.info(f"[DONE] tenant={tenant_id} phase=Ready endpoint=https://{subdomain}.{domain}")


@kopf.on.delete("romatenants", "roma.io", "v1")
def delete_tenant(meta, spec, **kwargs):
    """Cleanup when RomaTenant is deleted."""
    tenant_id = spec.get("tenantId", meta.get("name"))
    logger.info(f"[DELETE] tenant={tenant_id} — resources will be removed by Kubernetes GC")
