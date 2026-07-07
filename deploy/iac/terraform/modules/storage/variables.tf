variable "cluster_name"        { type = string }
variable "ceph_subnet"        { type = string }
variable "mon_hosts"          { type = list(string) }
variable "osd_devices"        { type = map(list(string)) }
variable "replication_factor"{ type = number }
variable "cluster_fsid"      { type = string }
