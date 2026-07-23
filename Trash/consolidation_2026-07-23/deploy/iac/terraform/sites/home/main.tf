# Home cluster — RTX 3060 + RK3576 Terraform site
# Uses parent vars + modules

module "network" {
  source = "../../modules/network"

  vlans = {
    mgmt  = { id = 10, subnet = "10.10.10.0/24", gateway = "10.10.10.1", pool_start = "100", pool_end = "200" }
    gpu   = { id = 20, subnet = "10.20.20.0/24", gateway = "10.20.20.1", pool_start = "100", pool_end = "200" }
    ceph  = { id = 30, subnet = "10.30.30.0/24", gateway = "10.30.30.1", pool_start = "100", pool_end = "200" }
    k8s   = { id = 40, subnet = "10.40.40.0/24", gateway = "10.40.40.1", pool_start = "100", pool_end = "200" }
  }

  node_leases = {
    rtx-node     = { mac = "XX:XX:XX:XX:XX:XX", vlan = "gpu" }
    rk3576-edge  = { mac = "YY:YY:YY:YY:YY:YY", vlan = "gpu" }
  }
}

module "vpn_mesh" {
  source = "../../modules/vpn_mesh"

  count      = length(var.nodes)
  node_name   = keys(var.nodes)[count.index]
  wg_ip      = "10.99.99.${10 + count.index}0"
  private_key = var.wireguard_peers[keys(var.nodes)[count.index]].private_key
  peers       = var.wireguard_peers
}
