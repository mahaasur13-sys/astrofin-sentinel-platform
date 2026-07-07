variable "minio_version" { description = "MinIO server version tag" }
variable "minio_user"     { description = "MinIO root user" }
variable "minio_pass"     { description = "MinIO root password (use SOPS in production)" }
variable "minio_port"     { description = "MinIO API port" }
variable "data_dir"       { description = "Host path for MinIO data" }
variable "minio_cpu"      { description = "CPU request" }
variable "minio_ram"      { description = "RAM request" }
