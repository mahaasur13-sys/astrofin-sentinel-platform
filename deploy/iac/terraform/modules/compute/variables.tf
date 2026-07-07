variable "node_name"  { type = string }
variable "node_ip"   { type = string }
variable "node_role" { type = string }
variable "gpu_count" { type = number }
variable "gpu_type"  { type = string }
variable "labels"   { type = map(string) }
