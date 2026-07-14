output "vlan100_gateway" {
  description = "VLAN 100 management gateway IP"
  value       = "${var.vlan100_subnet}.1"
}

output "vlan200_gateway" {
  description = "VLAN 200 GPU compute gateway IP"
  value       = "${var.vlan200_subnet}.1"
}

output "vlan100_dhcp_range" {
  description = "VLAN 100 DHCP pool range"
  value       = "${var.vlan100_subnet}.10 - ${var.vlan100_subnet}.250"
}

output "vlan200_dhcp_range" {
  description = "VLAN 200 DHCP pool range"
  value       = "${var.vlan200_subnet}.10 - ${var.vlan200_subnet}.250"
}

output "mikrotik_api_endpoint" {
  description = "MikroTik API endpoint for Ansible/other tools"
  value       = "https://${var.mikrotik_host}/rest"
}