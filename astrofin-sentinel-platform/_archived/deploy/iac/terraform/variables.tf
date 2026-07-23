# ============================================================
# Variables — home-cluster-iac
# ============================================================

# ── MinIO / S3 Backend ──────────────────────────────────────────────────────
variable "minio_access_key" {
  description = "MinIO access key for Terraform S3 backend state storage"
  type        = string
  default     = "minioadmin"
  sensitive   = true
}

variable "minio_secret_key" {
  description = "MinIO secret key for Terraform S3 backend state storage"
  type        = string
  default     = "minioadmin"
  sensitive   = true
}

# ── Network ─────────────────────────────────────────────────
variable "mesh_vpn_subnet" {
  description = "WireGuard/AmneziaWG mesh overlay subnet (CIDR)"
  type        = string
  default     = "10.200.0.0/16"
}

variable "vlan_segments" {
  description = "VLAN segments for network isolation"
  type = map(object({
    id       = number
    subnet   = string
    desc     = string
  }))
  default = {
    mgmt   = { id = 10,  subnet = "192.168.10.0/24", desc = "Management VLAN" }
    compute= { id = 20,  subnet = "192.168.20.0/24", desc = "Compute/Cluster VLAN" }
    storage= { id = 30,  subnet = "192.168.30.0/24", desc = "Ceph/storage VLAN" }
    edge   = { id = 40,  subnet = "192.168.40.0/24", desc = "Edge devices VLAN" }
  }
}

variable "wireguard_port" {
  description = "WireGuard mesh listen port"
  type        = number
  default     = 51820
}

# ── MikroTik ────────────────────────────────────────────────
variable "mikrotik_host" {
  description = "MikroTik API host"
  type        = string
  default     = "192.168.1.1"
  sensitive   = true
}

variable "mikrotik_user" {
  description = "MikroTik API username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "mikrotik_password" {
  description = "MikroTik API password"
  type        = string
  sensitive   = true
}

# ── Node IPs ────────────────────────────────────────────────
variable "home_node_ip" {
  description = "Primary node (RTX 3060) static IP"
  type        = string
  default     = "192.168.20.10"
}

variable "edge_node_ip" {
  description = "Edge node (RK3576) static IP"
  type        = string
  default     = "192.168.20.11"
}

variable "home_endpoint" {
  description = "Primary node public endpoint (or :0 for auto)"
  type        = string
  default     = ""
}

variable "edge_endpoint" {
  description = "Edge node public endpoint (or :0 for auto)"
  type        = string
  default     = ""
}

variable "home_wg_pubkey" {
  description = "Home node WireGuard public key"
  type        = string
  default     = ""
}

variable "edge_wg_pubkey" {
  description = "Edge node WireGuard public key"
  type        = string
  default     = ""
}

# ── Ceph ────────────────────────────────────────────────────
variable "ceph_subnet" {
  description = "Ceph cluster network subnet"
  type        = string
  default     = "192.168.30.0/24"
}

variable "ceph_osd_devices" {
  description = "Block devices to use as Ceph OSDs (per node)"
  type = map(list(string))
  default = {
    "home-rtx3060" = ["/dev/sdb"]
    "edge-rk3576"  = ["/dev/sdb"]
  }
}

variable "ceph_replication_factor" {
  description = "Ceph replication factor (min 2 for 2-node cluster)"
  type        = number
  default     = 2
}

variable "ceph_fsid" {
  description = "Ceph cluster FSID (generate with: uuidgen)"
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

# ── Slurm ───────────────────────────────────────────────────
variable "slurm_cluster_name" {
  description = "Slurm cluster name"
  type        = string
  default     = "home-cluster"
}

variable "slurm_control_host" {
  description = "Slurm primary controller host"
  type        = string
  default     = "192.168.20.10"
}

# ── Ray ─────────────────────────────────────────────────────
variable "ray_head_port" {
  description = "Ray head node GCS port"
  type        = number
  default     = 6379
}

# ── GPU ─────────────────────────────────────────────────────
variable "rtx_gpu_count" {
  description = "Number of GPUs on primary (RTX) node"
  type        = number
  default     = 1
}

variable "rtx_gpu_model" {
  description = "GPU model on primary (RTX) node"
  type        = string
  default     = "RTX 3060"
}
