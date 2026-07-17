# ============================================================
# Module: compute — Node definitions (physical or VM)
# ============================================================

resource "null_resource" "node_${node_name}" {
  triggers = {
    name  = var.node_name
    ip    = var.node_ip
    role  = var.node_role
    labels = jsonencode(var.labels)
  }

  # Static node inventory (physical nodes managed manually)
  # Terraform does NOT manage the OS on bare-metal nodes
}

# ── Node labels / attributes ────────────────────────────────
output "node_info" {
  value = {
    name      = var.node_name
    ip        = var.node_ip
    role      = var.node_role
    gpu_count = var.gpu_count
    gpu_type  = var.gpu_type
    labels    = var.labels
  }
}
