# Role: wireguard

Installs WireGuard mesh VPN overlay.

## Variables

```yaml
wireguard_port: 51820
wireguard_peers:
  - pubkey: "<peer-public-key>"
    endpoint: "<peer-public-ip>:51820"
    allowed_ips: "10.200.0.0/16"
```

## Usage

```bash
ansible-playbook -i inventory.ini playbook.yml --tags vpn
```
