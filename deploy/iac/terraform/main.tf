# Terraform main configuration for home-cluster-iac
# Distributed mini-AWS: Ceph + Slurm + Ray + K8s + AmneziaWG

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  # NOTE: backend "s3" is configured in ./backend.tf
  # Do NOT define a backend here — it lives in backend.tf for S3/MinIO
}

provider "local" {}
provider "null" {}

# ==========================================
# Variables
# ==========================================

variable "cluster_name" {
  description = "Name of the cluster"
  type        = string
  default     = "home-cluster"
}

variable "network_cidr" {
  description = "Internal network CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vlan_id" {
  description = "VLAN ID for cluster network"
  type        = number
  default     = 100
}

variable "nodes" {
  description = "Cluster nodes configuration"
  type = map(object({
    role       = string  # rtx3060 | rk3576 | ceph | k8s | router
    ip         = string
    gpu        = bool
    cpu_cores  = number
    memory_gb  = number
  }))
  default = {
    rtx-node = {
      role      = "rtx3060"
      ip        = "10.0.1.10"
      gpu       = true
      cpu_cores = 8
      memory_gb = 32
    }
    edge-node = {
      role      = "rk3576"
      ip        = "10.0.1.20"
      gpu       = false
      cpu_cores = 6
      memory_gb = 8
    }
    ceph-node-1 = {
      role      = "ceph"
      ip        = "10.0.1.30"
      gpu       = false
      cpu_cores = 4
      memory_gb = 16
    }
    ceph-node-2 = {
      role      = "ceph"
      ip        = "10.0.1.31"
      gpu       = false
      cpu_cores = 4
      memory_gb = 16
    }
  }
}

# Derived: collect Ceph nodes from var.nodes
locals {
  ceph_nodes = { for k, v in var.nodes : k => v if v.role == "ceph" }
  ceph_node_list = values(local.ceph_nodes)
  ceph_mon_hosts = [for n in local.ceph_node_list : n.ip]
}

# ==========================================
# Resources
# ==========================================

# MikroTik configuration
module "mikrotik" {
  source = "./modules/mikrotik"

  cluster_name = var.cluster_name
  network_cidr = var.network_cidr
  vlan_id      = var.vlan_id
}

# Ceph storage cluster (uses ./modules/storage)
module "ceph" {
  source = "./modules/storage"

  cluster_name        = var.cluster_name
  ceph_subnet         = var.network_cidr
  mon_hosts           = local.ceph_mon_hosts
  osd_devices         = var.ceph_osd_devices
  replication_factor  = var.ceph_replication_factor
  cluster_fsid        = var.ceph_fsid
}

# Slurm cluster
module "slurm" {
  source = "./modules/slurm"

  slurm_cluster_name = var.cluster_name
  controller_ips     = [var.nodes["rtx-node"].ip]
  compute_ips        = [var.nodes["edge-node"].ip]
}

# Kubernetes cluster
module "k8s" {
  source = "./modules/k8s"

  cluster_name = var.cluster_name
  network_cidr = var.network_cidr
}

# WireGuard mesh (AmneziaWG)
module "wireguard" {
  source = "./modules/vpn_mesh"

  cluster_name = var.cluster_name
  nodes        = var.nodes
  network_cidr = var.network_cidr
}

# ==========================================
# Outputs
# ==========================================

output "cluster_info" {
  description = "Cluster information"
  value = {
    name         = var.cluster_name
    network_cidr = var.network_cidr
    vlan_id      = var.vlan_id
    node_count   = length(var.nodes)
  }
}

output "node_ips" {
  description = "Node IP addresses"
  value = { for k, v in var.nodes : k => v.ip }
}

output "ceph_mon_hosts" {
  description = "Ceph monitor hosts"
  value       = local.ceph_mon_hosts
}
