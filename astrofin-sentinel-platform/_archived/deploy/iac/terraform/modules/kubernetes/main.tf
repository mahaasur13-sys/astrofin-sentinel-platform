# ============================================================
# Module: kubernetes — K8s lightweight layer over Slurm
# ============================================================

variable "k8s_cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "home-k8s"
}

variable "k8s_api_server_ip" {
  description = "IP for K8s API server (Slurm head node)"
  type        = string
}

variable "k8s_pod_subnet" {
  description = "Pod network CIDR (must not overlap with host network)"
  type        = string
  default     = "10.244.0.0/16"
}

variable "k8s_service_subnet" {
  description = "Service network CIDR"
  type        = string
  default     = "10.96.0.0/12"
}

variable "k8s_worker_nodes" {
  description = "List of worker node IPs"
  type        = list(string)
  default     = []
}

variable "enable_k8s" {
  description = "Whether to deploy K8s layer"
  type        = bool
  default     = false
}

# ── K8s control plane (lightweight, on Slurm head) ────────────
resource "null_resource" "k8s_control_plane" {
  count = var.enable_k8s ? 1 : 0

  triggers = {
    cluster_name   = var.k8s_cluster_name
    api_server_ip  = var.k8s_api_server_ip
    pod_subnet     = var.k8s_pod_subnet
    service_subnet = var.k8s_service_subnet
  }
}

# ── K8s workers ───────────────────────────────────────────────
resource "null_resource" "k8s_worker" {
  count = var.enable_k8s ? length(var.k8s_worker_nodes) : 0

  triggers = {
    cluster_name = var.k8s_cluster_name
    worker_ip    = var.k8s_worker_nodes[count.index]
    worker_index = count.index
  }
}

# ── Outputs ──────────────────────────────────────────────────
output "k8s_cluster_info" {
  description = "K8s cluster metadata"
  value = {
    cluster_name    = var.k8s_cluster_name
    api_server_ip   = var.enable_k8s ? var.k8s_api_server_ip : null
    pod_subnet      = var.k8s_pod_subnet
    service_subnet  = var.k8s_service_subnet
    workers         = var.k8s_worker_nodes
    enabled         = var.enable_k8s
  }
}
