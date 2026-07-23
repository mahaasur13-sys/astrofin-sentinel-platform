# Role: ceph

Deploys a 2-node Ceph storage cluster with replication factor 2.

## Variables

```yaml
ceph_cluster_network: "192.168.30.0/24"
ceph_public_network:  "192.168.30.0/24"
ceph_osd_devices: [sdb]
```

## Notes

- 2-node clusters cannot use replication=3. Use replication=2.
- OSD failure on a 2-node cluster can trigger pool degraded state.
- For production, a 3rd monitor/OSD node is recommended.
