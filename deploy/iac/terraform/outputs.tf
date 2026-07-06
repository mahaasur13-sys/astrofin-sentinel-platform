# ============================================================
# Outputs — home-cluster-iac
# ============================================================
# NOTE: Outputs are aligned with scripts/generate-inventory.sh
#       Run: cd terraform && terraform output --json | ../scripts/generate-inventory.sh
# ============================================================

#--- Network ---
output "mesh_vpn_subnet" {
  description = "WireGuard/AmneziaWG mesh overlay CIDR"
  value       = var.mesh_vpn_subnet
}

#--- VLAN segments (flat strings for Ansible inventory) ---
output "network_vlans" {
  description = "VLAN subnets as flat strings (for generate-inventory.sh)"
  value = {
    mgmt    = var.vlan_segments.mgmt.subnet
    compute = var.vlan_segments.compute.subnet
    storage = var.vlan_segments.storage.subnet
    vpn     = var.mesh_vpn_subnet
  }
}

#--- RTX Primary Node ---
output "rtx_node" {
  description = "RTX primary node — for Ansible inventory"
  value = {
    hostname   = "rtx-node"
    mgmt_ip    = var.home_node_ip
    compute_ip = replace(var.vlan_segments.compute.subnet, "/24", ".10")
    storage_ip = replace(var.vlan_segments.storage.subnet, "/24", ".10")
    vpn_ip     = cidrhost(var.mesh_vpn_subnet, 10)
    gpu_count  = var.rtx_gpu_count
    gpu_name   = var.rtx_gpu_model
    role       = "primary"
  }
}

#--- RK3576 Edge Node ---
output "rk3576_node" {
  description = "RK3576 edge node — for Ansible inventory"
  value = {
    hostname   = "rk3576-node"
    mgmt_ip    = var.edge_node_ip
    compute_ip = replace(var.vlan_segments.compute.subnet, "/24", ".11")
    vpn_ip     = cidrhost(var.mesh_vpn_subnet, 11)
    role       = "edge"
  }
}

#--- Node Summary (human-readable) ---
output "node_summary" {
  description = "Cluster node inventory"
  value = {
    home = {
      ip      = var.home_node_ip
      role    = "primary"
      gpu     = var.rtx_gpu_model
      mesh_ip = cidrhost(var.mesh_vpn_subnet, 10)
    }
    edge = {
      ip      = var.edge_node_ip
      role    = "edge"
      gpu     = "none"
      mesh_ip = cidrhost(var.mesh_vpn_subnet, 11)
    }
  }
}

#--- Ceph ---
output "ceph_info" {
  description = "Ceph cluster info"
  value = {
    mon_host   = var.ceph_subnet
    replicas   = var.ceph_replication_factor
    fsid       = var.ceph_fsid
  }
}

#--- Slurm ---
output "slurm_endpoints" {
  description = "Slurm controller endpoints"
  value = {
    control_host = var.slurm_control_host
    cluster_name = var.slurm_cluster_name
  }
}

#--- K3s ---
output "k3s_token" {
  description = "K3s join token (set by day2 script after install)"
  value       = "REPLACEME"
  sensitive   = true
}
