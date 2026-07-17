# Ceph Storage

## 2-Node Ceph Cluster

| Node | OSD | MON | Role |
|------|-----|-----|------|
| rtx-node | /dev/sdb | ✓ | Primary MON + OSD |
| rk3576-edge | /dev/sdb | ✓ | Secondary MON + OSD |

## Pool Configuration

| Pool | PG | PGP | Replicas | Use |
|------|----|----|----------|-----|
| vms | 128 | 128 | 2 | VM disks |
| shared | 128 | 128 | 2 | Shared data |
| backups | 128 | 128 | 2 | Backups |

## RBD Usage

```bash
# Create image
rbd create vms/myvm --size 50G --pool vms

# Map image
rbd map vms/myvm

# Mount
mount /dev/rbd0 /mnt/cephshared
```

## CephFS

```bash
# Mount CephFS
mount.ceph 10.20.20.10:/ /mnt/cephshared \
  -o name=admin,secretfile=/etc/ceph/ceph.client.admin.keyring
```
