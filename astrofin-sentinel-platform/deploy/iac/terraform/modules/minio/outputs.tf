output "minio_url"   { value = "http://localhost:${var.minio_port}" }
output "minio_bucket" { value = "velero" }
output "minio_console" { value = "http://localhost:9099" }
