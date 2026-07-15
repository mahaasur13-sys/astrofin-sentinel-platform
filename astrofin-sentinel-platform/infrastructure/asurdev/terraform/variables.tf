# =============================================================================
# VARIABLES — Home Cluster IaC
# =============================================================================

variable "cluster_name" {
  description = "Cluster identifier"
  type        = string
  default     = "home-cluster"
}

# -----------------------------------------------------------------------------
# Network — VLAN subnets
# -----------------------------------------------------------------------------
variable "mgmt_subnet" {
  description = "Management VLAN subnet"
  type        = string
  default     = "10.10.10.0/24"
}

variable "compute_subnet" {
  description = "Compute VLAN (Slurm/Ray) subnet"
  type        = string
  default     = "10.20.20.0/24"
}

variable "storage_subnet" {
  description = "Storage VLAN (Ceph) subnet"
  type        = string
  default     = "10.30.30.0/24"
}

variable "vpn_subnet" {
  description = "VPN mesh (WireGuard) subnet"
  type        = string
  default     = "10.40.40.0/24"
}

# -----------------------------------------------------------------------------
# Node definitions
# -----------------------------------------------------------------------------
variable "rtx_node" {
  description = "RTX 3060 PC — GPU compute node"
  type = object({
    hostname  = string
    ip_mgmt   = string
    ip_compute = string
    ip_storage = string
    ip_vpn    = string
    gpu_count = number
    cpu_cores = number
    ram_gb    = number
  })
  default = {
    hostname   = "rtx-node"
    ip_mgmt    = "10.10.10.10"
    ip_compute = "10.20.20.10"
    ip_storage = "10.30.30.10"
    ip_vpn     = "10.40.40.10"
    gpu_count  = 1
    cpu_cores  = 12
    ram_gb     = 32
  }
}

variable "rk3576_node" {
  description = "RK3576 — ARM edge node"
  type = object({
    hostname   = string
    ip_mgmt    = string
    ip_compute = string
    ip_vpn     = string
    cpu_cores  = number
    ram_gb     = number
  })
  default = {
    hostname   = "rk3576-node"
    ip_mgmt    = "10.10.10.20"
    ip_compute = "10.20.20.20"
    ip_vpn     = "10.40.40.20"
    cpu_cores  = 8
    ram_gb     = 8
  }
}

variable "vps_node" {
  description = "Optional VPS — HA backup / Ceph monitor"
  type = object({
    enabled    = bool
    ip_vpn     = string
    public_ip  = string
    hostname   = string
  })
  default = {
    enabled    = false
    ip_vpn     = "10.40.40.30"
    public_ip  = ""
    hostname   = "vps-node"
  }
}

# -----------------------------------------------------------------------------
# MikroTik
# -----------------------------------------------------------------------------
variable "mikrotik" {
  description = "MikroTik hEX S configuration"
  type = object({
    ip_mgmt    = string
    ip_compute = string
    ip_storage = string
    ip_vpn     = string
    ssh_user   = string
    ssh_port   = number
  })
  default = {
    ip_mgmt    = "10.10.10.1"
    ip_compute = "10.20.20.1"
    ip_storage = "10.30.30.1"
    ip_vpn     = "10.40.40.1"
    ssh_user   = "admin"
    ssh_port   = 22
  }
}

# -----------------------------------------------------------------------------
# Ceph
# -----------------------------------------------------------------------------
variable "ceph" {
  description = "Ceph cluster settings"
  type = object({
    fsid               = string
    mon_count          = number
    osd_replication    = number
    public_network     = string
    cluster_network    = string
  })
  default = {
    fsid           = "a3f2c8e1-7b9d-4e5f-8c1a-2b3d4e5f6a7b"
    mon_count       = 2
    osd_replication = 2
    public_network   = "10.30.30.0/24"
    cluster_network  = "10.30.30.0/24"
  }
}

# -----------------------------------------------------------------------------
# Slurm
# -----------------------------------------------------------------------------
variable "slurm" {
  description = "Slurm cluster settings"
  type = object({
    cluster_name    = string
    control_node    = string
    gpu_partition   = string
    cpu_partition   = string
  })
  default = {
    cluster_name  = "home-cluster"
    control_node  = "rtx-node"
    gpu_partition = "gpu"
    cpu_partition = "cpu"
  }
}

# -----------------------------------------------------------------------------
# Ray
# -----------------------------------------------------------------------------
variable "ray" {
  description = "Ray cluster settings"
  type = object({
    head_ip         = string
    dashboard_port  = number
    redis_port      = number
  })
  default = {
    head_ip        = "10.20.20.10"
    dashboard_port = 8265
    redis_port     = 6379
  }
}

# -----------------------------------------------------------------------------
# WireGuard
# -----------------------------------------------------------------------------
variable "wireguard" {
  description = "WireGuard mesh settings"
  type = object({
    listen_port    = number
    internal_net   = string
  })
  default = {
    listen_port   = 51820
    internal_net  = "10.40.40.0/24"
  }
}
