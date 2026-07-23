# Ansible inventory template — Terraform generates this
[rtx_node]
${rtx_ip} hostname=rtx-node

[rk3576_node]
${rk3576_ip} hostname=rk3576-node

${vps_ip != "" ? "[vps_node]\n${vps_ip} hostname=vps-node\n" : ""}

[all:vars]
cluster_name=${cluster_name}
ansible_user=root
ansible_python_interpreter=/usr/bin/python3
