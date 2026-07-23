apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Values.rbac.namespace }}
  labels:
    app.kubernetes.io/name: atom-os
    app.kubernetes.io/version: "7.0"
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Values.rbac.operatorServiceAccount }}
  namespace: {{ .Values.rbac.namespace }}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: atom-operator
  labels:
    app.kubernetes.io/name: atom-operator
    app.kubernetes.io/version: "7.0"
rules:
  - apiGroups: ["atom.io"]
    resources: ["atomclusters", "atomclusters/status"]
    verbs: ["get", "list", "watch", "patch", "update", "create", "delete"]
  - apiGroups: ["apps"]
    resources: ["statefulsets", "statefulsets/status", "statefulsets/finalizers"]
    verbs: ["get", "list", "watch", "create", "patch", "update", "delete"]
  - apiGroups: [""]
    resources: ["services", "services/status", "pods", "serviceaccounts", "events"]
    verbs: ["get", "list", "watch", "create", "patch", "update", "delete"]
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: atom-operator
roleRef:
  kind: ClusterRole
  name: atom-operator
subjects:
  - kind: ServiceAccount
    name: {{ .Values.rbac.operatorServiceAccount }}
    namespace: {{ .Values.rbac.namespace }}
