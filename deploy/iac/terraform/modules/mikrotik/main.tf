# MikroTik RouterOS configuration generator
# Produces ROS script for VLAN/DHCP/Firewall setup

resource "local_file" "mikrotik_script" {
  filename = "${path.module}/mikrotik-setup.rsc"
  content   = <<-EOT
# MikroTik RouterOS — home-cluster VLAN setup
# =============================================
# Generator: Terraform (home-cluster-iac)
# Target: hEX S (E60iUGS) or any RouterOS 7.x

/system identity set name="home-cluster-router"

/interface vlan
add name=vlan-mgmt   vlan-id=${var.vlan_id} interface=bridge
add name=vlan-compute vlan-id=${var.vlan_id + 10} interface=bridge
add name=vlan-storage vlan-id=${var.vlan_id + 20} interface=bridge
add name=vlan-edge    vlan-id=${var.vlan_id + 30} interface=bridge

/ip pool
add name=pool-mgmt   ranges=192.168.10.100-192.168.10.200
add name=pool-compute ranges=192.168.20.100-192.168.20.200
add name=pool-storage ranges=192.168.30.100-192.168.30.200
add name=pool-edge    ranges=192.168.40.100-192.168.40.200

/ip dhcp-server
add address-pool=pool-mgmt   interface=vlan-mgmt   name=dhcp-mgmt
add address-pool=pool-compute interface=vlan-compute name=dhcp-compute
add address-pool=pool-storage interface=vlan-storage name=dhcp-storage
add address-pool=pool-edge    interface=vlan-edge    name=dhcp-edge

/ip firewall nat
add chain=srcnat out-interface-list=WAN action=masquerade

/ip firewall filter
add chain=forward action=accept connection-state=established,related comment="Allow established"
add chain=forward action=drop connection-state=invalid comment="Drop invalid"

/routing ospf network
add network=${var.network_cidr} area=backbone
EOT
}

output "setup_script" {
  description = "RouterOS script to apply on MikroTik"
  value       = resource.local_file.mikrotik_script.content
}
