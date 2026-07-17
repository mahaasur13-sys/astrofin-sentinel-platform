# ============================================================
# Module: ray — Ray AI runtime (head + workers)
# ============================================================

variable "ray_cluster_name" {
  description = "Ray cluster name"
  type        = string
  default     = "home-ray"
}

variable "ray_head_ip" {
  description = "IP of Ray head node"
  type        = string
}

variable "ray_worker_ips" {
  description = "IP addresses of Ray worker nodes"
  type        = list(string)
}

variable "ray_dashboard_port" {
  description = "Ray dashboard port"
  type        = number
  default     = 8265
}

variable "ray_worker_gpu_count" {
  description = "Number of GPUs per worker node"
  type        = number
  default     = 0
}

# ── Ray head node ─────────────────────────────────────────────
resource "null_resource" "ray_head" {
  triggers = {
    cluster_name = var.ray_cluster_name
    head_ip      = var.ray_head_ip
    dashboard_port = var.ray_dashboard_port
  }
}

# ── Ray workers ───────────────────────────────────────────────
resource "null_resource" "ray_worker" {
  count = length(var.ray_worker_ips)

  triggers = {
    cluster_name  = var.ray_cluster_name
    worker_ip     = var.ray_worker_ips[count.index]
    worker_index  = count.index
    gpu_count     = var.ray_worker_gpu_count
  }
}

# ── Outputs ──────────────────────────────────────────────────
output "ray_cluster_info" {
  description = "Ray cluster metadata"
  value = {
    cluster_name    = var.ray_cluster_name
    head_ip         = var.ray_head_ip
    workers         = var.ray_worker_ips
    dashboard_url   = "http://${var.ray_head_ip}:${var.ray_dashboard_port}"
    dashboard_port  = var.ray_dashboard_port
  }
}

output "ray_head_ip" {
  description = "Ray head node IP"
  value       = var.ray_head_ip
}

output "ray_worker_ips" {
  description = "Ray worker node IPs"
  value       = var.ray_worker_ips
}
