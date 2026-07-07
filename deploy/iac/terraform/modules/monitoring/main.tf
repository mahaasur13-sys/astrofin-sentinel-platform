# ============================================================
# Module: monitoring — Prometheus + Loki + Grafana stack
# ============================================================

variable "monitoring_cluster_name" {
  description = "Monitoring stack name"
  type        = string
  default     = "home-monitoring"
}

variable "prometheus_host" {
  description = "Host IP for Prometheus"
  type        = string
}

variable "grafana_host" {
  description = "Host IP for Grafana"
  type        = string
}

variable "loki_host" {
  description = "Host IP for Loki"
  type        = string
}

variable "prometheus_port" {
  description = "Prometheus port"
  type        = number
  default     = 9090
}

variable "grafana_port" {
  description = "Grafana port"
  type        = number
  default     = 3000
}

variable "loki_port" {
  description = "Loki port"
  type        = number
  default     = 3100
}

variable "scrape_configs" {
  description = "Prometheus scrape configs (node exporters, etc.)"
  type        = list(any)
  default     = []
}

# ── Monitoring hosts ──────────────────────────────────────────
resource "null_resource" "prometheus_instance" {
  triggers = {
    monitoring_name = var.monitoring_cluster_name
    host            = var.prometheus_host
    port            = var.prometheus_port
  }
}

resource "null_resource" "grafana_instance" {
  triggers = {
    monitoring_name = var.monitoring_cluster_name
    host            = var.grafana_host
    port            = var.grafana_port
  }
}

resource "null_resource" "loki_instance" {
  triggers = {
    monitoring_name = var.monitoring_cluster_name
    host            = var.loki_host
    port            = var.loki_port
  }
}

# ── Outputs ──────────────────────────────────────────────────
output "monitoring_endpoints" {
  description = "Monitoring stack endpoints"
  value = {
    prometheus = "http://${var.prometheus_host}:${var.prometheus_port}"
    grafana    = "http://${var.grafana_host}:${var.grafana_port}"
    loki       = "http://${var.loki_host}:${var.loki_port}"
  }
}
