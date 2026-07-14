variable "mikrotik_host" {
  description = "MikroTik API endpoint (IP or hostname)"
  type        = string
  default     = "192.168.1.1"
}

variable "mikrotik_user" {
  description = "MikroTik API username"
  type        = string
  default     = "admin"
}

variable "mikrotik_password" {
  description = "MikroTik API password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vlan100_subnet" {
  description = "VLAN 100 management subnet (CIDR notation)"
  type        = string
  default     = "10.66.100.0"
}

variable "vlan200_subnet" {
  description = "VLAN 200 GPU compute subnet (CIDR notation)"
  type        = string
  default     = "10.66.200.0"
}

variable "dns_servers" {
  description = "DNS servers for DHCP clients"
  type        = string
  default     = "1.1.1.1,8.8.8.8"
}

variable "mesh_subnet" {
  description = "WireGuard mesh VPN subnet"
  type        = string
  default     = "10.66.0.0/16"
}

variable "mesh_gateway" {
  description = "Mesh gateway IP (RTX gpu-node)"
  type        = string
  default     = "10.66.0.10"
}