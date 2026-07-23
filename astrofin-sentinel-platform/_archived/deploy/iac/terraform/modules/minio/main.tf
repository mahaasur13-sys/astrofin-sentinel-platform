# MinIO S3-compatible storage for Velero backups
# Usage:
#   module "minio" {
#     source = "./modules/minio"
#     minio_version = "RELEASE.2024-01-16T16-07-38Z"
#   }

variable "minio_version" {
  default = "RELEASE.2024-01-16T16-07-38Z"
}

variable "minio_user" { default = "minioadmin" }
variable "minio_pass" { default = "minioadmin" }
variable "minio_port" { default = 9000 }
variable "data_dir"   { default = "/opt/minio/data" }
variable "minio_cpu"  { default = "1" }
variable "minio_ram"  { default = "2Gi" }

resource "null_resource" "minio_install" {
  # Docker-based MinIO (assumes Docker installed on target)
  provisioner "local-exec" {
    command = <<-EOT
      docker run -d \
        --name minio \
        --restart unless-stopped \
        -p ${var.minio_port}:9000 \
        -p 9099:9099 \
        -e MINIO_ROOT_USER=${var.minio_user} \
        -e MINIO_ROOT_PASSWORD=${var.minio_pass} \
        -v ${var.data_dir}:/data \
        minio/minio:${var.minio_version} \
        server /data --console-address ":9099"
    EOT
  }
}

resource "null_resource" "minio_bucket" {
  depends_on = [null_resource.minio_install]
  provisioner "local-exec" {
    command = <<-EOT
      sleep 5
      docker exec minio mc alias set local http://localhost:${var.minio_port} ${var.minio_user} ${var.minio_pass} 2>/dev/null || true
      docker exec minio mc mb local/velero --ignore-existing 2>/dev/null || true
      docker exec minio mc anonymous set download local/velero 2>/dev/null || true
    EOT
  }
}

output "minio_url" {
  value       = "http://localhost:${var.minio_port}"
  description = "MinIO server URL"
}

output "minio_bucket" {
  value = "velero"
}
