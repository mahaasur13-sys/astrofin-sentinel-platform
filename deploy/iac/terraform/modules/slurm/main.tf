# ============================================================
# Module: slurm — Slurm HA cluster (3-controller layout)
# ============================================================

variable "slurm_cluster_name" {
  description = "Slurm cluster name"
  type        = string
  default     = "home-slurm"
}

variable "controller_ips" {
  description = "IP addresses of Slurm controllers"
  type        = list(string)
}

variable "compute_ips" {
  description = "IP addresses of Slurm compute nodes"
  type        = list(string)
}

variable "slurm_user" {
  description = "Slurm OS user UID"
  type        = number
  default     = 984
}

variable "slurm_group" {
  description = "Slurm OS group GID"
  type        = number
  default     = 984
}

variable "gpu_partition_enabled" {
  description = "Enable GPU partition in Slurm"
  type        = bool
  default     = true
}

# ── Slurm controller cluster (primary + backup) ───────────────
resource "null_resource" "slurm_controller_primary" {
  count = 1

  triggers = {
    cluster_name = var.slurm_cluster_name
    controller_ip = var.controller_ips[0]
    role          = "primary"
  }
}

resource "null_resource" "slurm_controller_backup" {
  count = length(var.controller_ips) > 1 ? length(var.controller_ips) - 1 : 0

  triggers = {
    cluster_name = var.slurm_cluster_name
    controller_ip = var.controller_ips[count.index + 1]
    role          = "backup"
  }
}

# ── Slurm compute nodes ───────────────────────────────────────
resource "null_resource" "slurm_compute_node" {
  count = length(var.compute_ips)

  triggers = {
    cluster_name = var.slurm_cluster_name
    compute_ip   = var.compute_ips[count.index]
    gpu_count    = length(regexall("rtx|gtx|quadro", var.compute_ips[count.index])) > 0 ? 1 : 0
  }
}

# ── Slurm partitions ──────────────────────────────────────────
resource "null_resource" "slurm_partitions" {
  triggers = {
    gpu_partition_enabled = var.gpu_partition_enabled
    compute_count        = length(var.compute_ips)
  }
}

# ── Outputs ──────────────────────────────────────────────────
output "slurm_cluster_info" {
  description = "Slurm cluster metadata"
  value = {
    cluster_name      = var.slurm_cluster_name
    controllers       = var.controller_ips
    compute_nodes     = var.compute_ips
    gpu_partition     = var.gpu_partition_enabled ? "gpu" : null
    slurm_user_uid    = var.slurm_user
    slurm_group_gid   = var.slurm_group
  }
}

output "primary_controller_ip" {
  description = "Primary Slurm controller IP"
  value       = var.controller_ips[0]
}

output "gpu_nodes" {
  description = "Compute nodes with GPU"
  value       = [for i, ip in var.compute_ips : ip if i < length(var.compute_ips) && var.gpu_partition_enabled]
}
