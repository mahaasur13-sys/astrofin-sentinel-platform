# MikroTik RouterOS resource configuration
# Terraform provider: terraform-routeros/terraform-provider-routeros

resource "routeros_interface_bridge" "main_bridge" {
  name = "bridge-home-cluster"
  l2mtu = 1580
}

resource "routeros_interface_vlan" "vlan100_mgmt" {
  name     = "vlan100-mgmt"
  vlan_id  = 100
  interface = routeros_interface_bridge.main_bridge.name
}

resource "routeros_interface_vlan" "vlan200_gpu" {
  name     = "vlan200-gpu"
  vlan_id  = 200
  interface = routeros_interface_bridge.main_bridge.name
}

resource "routeros_ip_address" "vlan100_gateway" {
  address = "${var.vlan100_subnet}.1/24"
  interface = routeros_interface_vlan.vlan100_mgmt.name
  network  = var.vlan100_subnet
}

resource "routeros_ip_address" "vlan200_gateway" {
  address = "${var.vlan200_subnet}.1/24"
  interface = routeros_interface_vlan.vlan200_gpu.name
  network  = var.vlan200_subnet
}

# DHCP servers for each VLAN
resource "routeros_ip_pool" "vlan100_pool" {
  name = "pool-mgmt"
  ranges = ["${var.vlan100_subnet}.10-${var.vlan100_subnet}.250"]
}

resource "routeros_ip_pool" "vlan200_pool" {
  name = "pool-gpu"
  ranges = ["${var.vlan200_subnet}.10-${var.vlan200_subnet}.250"]
}

resource "routeros_ip_dhcp_server" "vlan100_dhcp" {
  name         = "dhcp-mgmt"
  interface    = routeros_interface_vlan.vlan100_mgmt.name
  address_pool = "pool-mgmt"
  disabled     = false

  dhcp_option {
    name  = "router"
    value = "${var.vlan100_subnet}.1"
  }

  dhcp_option {
    name  = "dns-server"
    value = var.dns_servers
  }
}

resource "routeros_ip_dhcp_server" "vlan200_dhcp" {
  name         = "dhcp-gpu"
  interface    = routeros_interface_vlan.vlan200_gpu.name
  address_pool = "pool-gpu"
  disabled     = false

  dhcp_option {
    name  = "router"
    value = "${var.vlan200_subnet}.1"
  }

  dhcp_option {
    name  = "dns-server"
    value = var.dns_servers
  }
}

# NAT masquerade for internet access
resource "routeros_ip_firewall_nat" "masquerade_vlan100" {
  chain     = "srcnat"
  out_interface = routeros_interface_vlan.vlan100_mgmt.name
  src_address = var.vlan100_subnet
  action     = "masquerade"
}

resource "routeros_ip_firewall_nat" "masquerade_vlan200" {
  chain     = "srcnat"
  out_interface = routeros_interface_vlan.vlan200_gpu.name
  src_address = var.vlan200_subnet
  action     = "masquerade"
}

# Firewall rules — basic security
resource "routeros_ip_firewall_filter" "accept_established" {
  chain      = "input"
  action     = "accept"
  connection_state = "established,related"
}

resource "routeros_ip_firewall_filter" "accept_vlan_traffic" {
  chain      = "input"
  src_address = var.vlan100_subnet
  dst_address = var.vlan200_subnet
  action     = "accept"
}

resource "routeros_ip_firewall_filter" "drop_invalid" {
  chain      = "input"
  connection_state = "invalid"
  action     = "drop"
}

# Route for mesh VPN
resource "routeros_ip_route" "mesh_route" {
  dst_address = var.mesh_subnet
  gateway     = var.mesh_gateway
}