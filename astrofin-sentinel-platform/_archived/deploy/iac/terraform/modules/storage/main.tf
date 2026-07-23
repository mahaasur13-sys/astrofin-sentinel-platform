# ============================================================
# Module: storage — Ceph 2-node cluster
# ============================================================

resource "null_resource" "ceph_cluster" {
  triggers = {
    cluster_name = var.cluster_name
    mon_hosts    = join(",", var.mon_hosts)
    replicas     = var.replication_factor
  }
}

# ── Ceph config (ansible/roles/ceph/templates/ceph.conf.j2) ──
# Generated as local file for reference
resource "local_file" "ceph_conf" {
  filename = "${path.module}/ceph.conf.generated"
  content  = <<-EOT
# ============================================================
# Ceph cluster config (generated)
# ============================================================
[global]
fsid                = ${var.cluster_fsid}
mon_initial_members = ${join(",", var.mon_hosts)}
mon_host            = ${join(",", var.mon_hosts)}
osd_pool_default_size       = ${var.replication_factor}
osd_pool_default_min_size   = 1
public_network     = ${var.ceph_subnet}
cluster_network    = ${var.ceph_subnet}
# 2-node pool settings
osd_crush_chooseleaf_types  = 0
EOT
}

output "ceph_info" {
  value = {
    cluster_name = var.cluster_name
    mon_hosts    = var.mon_hosts
    replicas     = var.replication_factor
    fsid         = var.cluster_fsid
  }
}
