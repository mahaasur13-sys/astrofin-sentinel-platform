# =============================================================================
# TERRAFORM OUTPUTS
# =============================================================================

output "cluster_info" {
  description = "Cluster summary"
  value = <<-EOF
  Cluster: ${var.cluster_name}
  Nodes: RTX=${var.rtx_node.ip_compute}, RK3576=${var.rk3576_node.ip_compute}
  VPN mesh: ${var.wireguard.internal_net}
  Storage: ${var.storage_subnet}
  EOF
}

output "rtx_node" {
  description = "RTX 3060 node info"
  value = {
    hostname = var.rtx_node.hostname
    mgmt_ip  = var.rtx_node.ip_mgmt
    compute_ip = var.rtx_node.ip_compute
    storage_ip = var.rtx_node.ip_storage
    vpn_ip  = var.rtx_node.ip_vpn
    gpu_count = var.rtx_node.gpu_count
  }
}

output "rk3576_node" {
  description = "RK3576 edge node info"
  value = {
    hostname = var.rk3576_node.hostname
    mgmt_ip  = var.rk3576_node.ip_mgmt
    compute_ip = var.rk3576_node.ip_compute
    vpn_ip  = var.rk3576_node.ip_vpn
  }
}

output "network_vlans" {
  description = "VLAN subnets"
  value = {
    mgmt    = var.mgmt_subnet
    compute = var.compute_subnet
    storage = var.storage_subnet
    vpn    = var.vpn_subnet
  }
}

output "slurm" {
  description = "Slurm connection info"
  value = {
    control_node = var.slurm.control_node
    gpu_partition = var.slurm.gpu_partition
    cpu_partition = var.slurm.cpu_partition
  }
}

output "ceph" {
  description = "Ceph storage info"
  value = {
    fsid = var.ceph.fsid
    public_network = var.ceph.public_network
    mon_count = var.ceph.mon_count
  }
}
