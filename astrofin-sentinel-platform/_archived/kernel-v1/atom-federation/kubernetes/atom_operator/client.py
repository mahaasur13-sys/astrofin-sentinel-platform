"""Kubernetes API client wrapper for ATOM operator."""

from __future__ import annotations

from kubernetes.client import ApiClient, AppsV1Api, CoreV1Api, CustomObjectsApi
from kubernetes.client.rest import ApiException

from kubernetes import client


class K8sClient:
    def __init__(self) -> None:
        self.api_client = ApiClient()
        self.core = CoreV1Api(self.api_client)
        self.apps = AppsV1Api(self.api_client)
        self.custom: CustomObjectsApi | None = None

    def refresh_custom_api(self) -> None:
        # CustomObjectsApi takes an ApiClient (not a DynamicClient). The shared
        # self.api_client already inherits the loaded Configuration from
        # config.load_incluster_config() / load_kube_config() that main() runs
        # before constructing this object, so no extra configuration plumbing
        # is required here. Building a DynamicClient eagerly probes /version
        # and would break startup when no live API server is reachable, so we
        # avoid it on this code path.
        if self.custom is None:
            self.custom = CustomObjectsApi(self.api_client)

    def get_cluster(
        self, name: str, namespace: str = "default"
    ) -> dict | None:
        self.refresh_custom_api()
        try:
            return self.custom.get_namespaced_custom_object(
                group="atom.io",
                version="v1",
                plural="atomclusters",
                name=name,
                namespace=namespace,
            )
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def list_clusters(self, namespace: str = "default") -> list[dict]:
        self.refresh_custom_api()
        try:
            result = self.custom.list_namespaced_custom_object(
                group="atom.io",
                version="v1",
                plural="atomclusters",
                namespace=namespace,
            )
            return result.get("items", [])
        except ApiException:
            return []

    def patch_status(
        self, name: str, namespace: str, status: dict
    ) -> dict:
        self.refresh_custom_api()
        patched = self.custom.patch_namespaced_custom_object_status(
            group="atom.io",
            version="v1",
            plural="atomclusters",
            name=name,
            namespace=namespace,
            body={"status": status},
        )
        return patched

    def patch_cluster(
        self, name: str, namespace: str, patch: dict
    ) -> dict:
        self.refresh_custom_api()
        return self.custom.patch_namespaced_custom_object(
            group="atom.io",
            version="v1",
            plural="atomclusters",
            name=name,
            namespace=namespace,
            body=patch,
        )

    def get_statefulset(
        self, name: str, namespace: str = "default"
    ) -> dict | None:
        try:
            return self.apps.read_namespaced_stateful_set(name, namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def create_statefulset(self, sts: dict) -> dict:
        return self.apps.create_namespaced_stateful_set(
            namespace=sts["metadata"]["namespace"], body=sts
        )

    def patch_statefulset(self, name: str, namespace: str, patch: dict) -> dict:
        return self.apps.patch_namespaced_stateful_set(
            name=name, namespace=namespace, body=patch
        )

    def read_statefulset(self, name: str, namespace: str) -> dict | None:
        try:
            return self.apps.read_namespaced_stateful_set(name, namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def get_service(
        self, name: str, namespace: str = "default"
    ) -> dict | None:
        try:
            return self.core.read_namespaced_service(name, namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def create_service(self, svc: dict) -> dict:
        return self.core.create_namespaced_service(
            namespace=svc["metadata"]["namespace"], body=svc
        )

    def patch_service(self, name: str, namespace: str, patch: dict) -> dict:
        return self.core.patch_namespaced_service(
            name=name, namespace=namespace, body=patch
        )

    def create_service_account(self, sa: dict) -> dict:
        return self.core.create_namespaced_service_account(
            namespace=sa["metadata"]["namespace"], body=sa
        )

    def create_cluster_role(self, cr: dict) -> dict:
        return client.RbacAuthorizationV1Api(self.api_client).create_cluster_role(body=cr)

    def create_cluster_role_binding(self, crb: dict) -> dict:
        return client.RbacAuthorizationV1Api(self.api_client).create_cluster_role_binding(body=crb)

    def ensure_service_account(self, name: str, namespace: str) -> str:
        try:
            self.core.read_namespaced_service_account(name, namespace)
        except ApiException:
            sa = {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {"name": name, "namespace": namespace},
            }
            self.create_service_account(sa)
        return name

    @property
    def rbac(self) -> client.RbacAuthorizationV1Api:
        return client.RbacAuthorizationV1Api(self.api_client)

    @property
    def apps_api(self) -> AppsV1Api:
        return self.apps

    @property
    def core_api(self) -> CoreV1Api:
        return self.core
