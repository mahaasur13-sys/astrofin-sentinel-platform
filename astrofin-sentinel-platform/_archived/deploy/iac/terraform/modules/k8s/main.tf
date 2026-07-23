# Kubernetes cluster definition
# NOTE: This is a declarative descriptor only.
# Actual k8s provisioning is handled by Ansible (kubespray or kubeadm).

resource "null_resource" "k8s_cluster" {
  triggers = {
    cluster_name = var.cluster_name
    network_cidr = var.network_cidr
  }
}

output "k8s_cluster_info" {
  value = {
    cluster_name = var.cluster_name
    network_cidr = var.network_cidr
    note         = "Provisioned via Ansible (kubespray)"
  }
}
