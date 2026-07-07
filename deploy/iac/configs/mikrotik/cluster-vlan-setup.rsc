# ============================================================
# MikroTik hEX S — Cluster VLAN Setup (Day 1)
# ============================================================
# Target:  RB760iGS / hEX S, RouterOS 7.x
# Purpose: Create 4 VLANs for cluster isolation
# Usage:   /file print; /file export file-name=cluster-vlan-setup.rsc
# ============================================================

# --- Variables (edit before running) ---
:local MIKROTIK_IP "10.10.10.1"
:local VLAN_MGMT     10
:local VLAN_COMPUTE  20
:local VLAN_STORAGE  30
:local VLAN_VPN     40

# ============================================================
# Create bridge with VLAN filtering
# ============================================================
/interface/bridge/add name=br-cluster vlan-filtering=yes disabled=no

# Add ether2-ether5 as trunk ports
:foreach port in={"ether2";"ether3";"ether4";"ether5"} do={
    /interface/bridge/port/add bridge=br-cluster interface=$port
}

# ============================================================
# Create VLANs
# ============================================================
/interface/vlan/add name=vlan10-mgmt    vlan-id=$VLAN_MGMT    interface=br-cluster
/interface/vlan/add name=vlan20-compute vlan-id=$VLAN_COMPUTE interface=br-cluster
/interface/vlan/add name=vlan30-storage vlan-id=$VLAN_STORAGE interface=br-cluster
/interface/vlan/add name=vlan40-vpn    vlan-id=$VLAN_VPN     interface=br-cluster

# ============================================================
# Assign IPs
# ============================================================
/ip/address/add address=10.10.10.1/24       interface=vlan10-mgmt
/ip/address/add address=10.20.20.1/24       interface=vlan20-compute
/ip/address/add address=10.30.30.1/24       interface=vlan30-storage
/ip/address/add address=10.40.40.1/24       interface=vlan40-vpn

# ============================================================
# DHCP server on mgmt VLAN (optional)
# ============================================================
/ip/pool/add name=pool-mgmt ranges=10.10.10.50-10.10.10.200
/ip/dhcp-server/add name=dhcp-mgmt interface=vlan10-mgmt address-pool=pool-mgmt disabled=no
/ip/dhcp-server/network/add address=10.10.10.0/24 gateway=10.10.10.1 dns-server=10.10.10.1

# ============================================================
# Firewall: allow established/related, drop input from outside
# ============================================================
/ip/firewall/filter/add chain=input action=accept connection-state=established,related
/ip/firewall/filter/add chain=input action=drop src-address=!10.10.10.0/24

# Allow ICMP (ping)
/ip/firewall/filter/add chain=input action=accept protocol=icmp

# ============================================================
# DNS for cluster.local domain
# ============================================================
/ip/dns/add servers=1.1.1.1,8.8.8.8 allow-remote-requests=yes
/ip/dns/static/add name=home-rtx3060 address=10.20.20.10 domain=home-rtx3060.cluster.local
/ip/dns/static/add name=edge-rk3576 address=10.20.20.11 domain=edge-rk3576.cluster.local

# ============================================================
# Enable SSH
# ============================================================
/ip/service/set name=ssh port=22 disabled=no

:put "============================================"
:put "[OK] Cluster VLANs created:"
:put "  VLAN 10 (mgmt)    -> 10.10.10.0/24"
:put "  VLAN 20 (compute) -> 10.20.20.0/24"
:put "  VLAN 30 (storage) -> 10.30.30.0/24"
:put "  VLAN 40 (vpn)     -> 10.40.40.0/24"
:put "============================================"
