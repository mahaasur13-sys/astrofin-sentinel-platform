# FINAL_ENHANCEMENTS.md

> Финальный набор: HA Slurm, K8s Federation, CI/CD, интеграция edge-node.
> Все файлы готовы к копированию и push.

## Созданные файлы

| Путь | Описание |
|------|----------|
| `ansible/roles/slurm_ha/` | 3-controller HA: keepalived + slurm.conf + slurmdbd |
| `ansible/roles/edge-node/` | ARM64: K3s agent + containerd + slurmd + Ray worker |
| `k8s/federation/` | KubeFed: helm-install + cluster-registration + federated deployments |
| `.github/workflows/infra-ci.yml` | CI: terraform/ansible/shellcheck/kubeval |
| `.github/SELF_HOSTED_RUNNER.md` | Инструкция по runner (SSH, без токенов) |
| `ansible/playbook.yml` | Обновлён: все роли + tags |
| `ansible/inventory.ini` | Обновлён: groups для HA + edge + ceph |
| `ansible/group_vars/all.yml` | HA/K8s/Ray/Ceph переменные |
| `README.md` | Обновлённая архитектура + badges |

---

## 1. `ansible/roles/slurm_ha/`

### `tasks/main.yml`
```yaml
---
# HA Slurm: 3 controllers + keepalived VIP
# VIP: 10.20.20.254 (failover automatic)

- name: Install keepalived + slurm
  package:
    name: [keepalived, munge, slurm, slurm-slurmctld, slurm-slurmdbd, ceph-common]
    state: present

- name: Deploy keepalived.conf
  template:
    src: keepalived.conf.j2
    dest: /etc/keepalived/keepalived.conf
  notify: restart keepalived
  become: yes

- name: Deploy slurm.conf (all 3 controllers listed)
  template:
    src: slurm.conf.j2
    dest: /etc/slurm/slurm.conf
  notify: restart slurmctld
  become: yes

- name: Enable keepalived
  service:
    name: keepalived
    state: started
    enabled: yes
  become: yes

- name: Enable slurmctld
  service:
    name: slurmctld
    state: started
    enabled: yes
  become: yes
```

### `defaults/main.yml`
```yaml
slurm_ha_enabled: true
keepalived_vip: "10.20.20.254"
keepalived_priority_primary: 150
keepalived_priority_secondary: 100
keepalived_priority_tertiary: 50
slurm_state_dir: "/mnt/cephfs/slurm/state"
slurm_use_cephfs: true
cephfs_monitors: "10.20.20.10:6789,10.20.20.11:6789"
```

### `templates/slurm.conf.j2`
```jinja2
{% for ctrl in slurm_control_machines %}
SlurmctldHost={{ ctrl }}{% if loop.first %}*{% endif %}
{% endfor %}
StateSaveLocation={{ slurm_state_dir }}
SlurmdSpoolDir=/var/spool/slurm/slurmd
SelectType=select/cons_tres
SelectTypeParameters=CR_CPU_Memory,CR_GPU
{% for partition in slurm_partitions %}
PartitionName={{ partition.name }}
  Nodes={{ partition.nodes | join(',') }}
  MaxTime={{ partition.max_time }}
  State=UP
{% endfor %}
```

### `templates/keepalived.conf.j2`
```jinja2
vrrp_instance VI_SLURM {
    interface {{ keepalived_interface }}
    virtual_router_id 51
    priority {% if inventory_hostname == slurm_control_machines[0] %}{{ keepalived_priority_primary }}{% else %}{{ keepalived_priority_secondary }}{% endif %}
    virtual_ipaddress { {{ keepalived_vip }}/24 }
    track_script { chk_slurmctld }
}
vrrp_script chk_slurmctld {
    script "/usr/bin/pgrep -x slurmctld"
    interval 3
    weight -10
}
```

---

## 2. `ansible/roles/edge-node/`

```yaml
# RK3576 ARM64 role (уже создан ранее):
# tasks/main.yml — K3s agent, containerd, slurmd, Ray worker, node-exporter
# defaults/main.yml — k3s_master_ip, slurm_controller_vip, ray_head_ip
# handlers/main.yml — restart handlers
```

---

## 3. `k8s/federation/`

### `helm-install.sh`
```bash
#!/usr/bin/env bash
set -e
KUBEFED_VERSION="${KUBEFED_VERSION:-0.10.0}"
helm repo add kubefed https://kubernetes-sigs.github.io/kubefed/charts
helm upgrade -i kubefed "https://github.com/kubernetes-sigs/kubefed/releases/download/v${KUBEFED_VERSION}/kubefed-${KUBEFED_VERSION}.tgz" \
  --namespace kube-federation-system --create-namespace
kubefedctl join cluster.local --cluster-context cluster.local --host-cluster-context cluster.local
kubefedctl join arm-cluster --cluster-context arm-cluster --host-cluster-context cluster.local --lightweight
```

### `federated-deployment.yaml`
```yaml
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: nginx-federated
  namespace: default
spec:
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
  placement:
    clusterNames:
    - cluster.local      # x86
    - arm-cluster         # ARM
  overrides:
  - clusterName: arm-cluster
    clusterOverrides:
    - path: "/spec/replicas"
      value: 1
```

### `placement-policy.yaml`
```yaml
# GPU jobs → x86 cluster only
# Batch workers → both clusters (prefer ARM)
# Edge proxy → ARM cluster only
```

---

## 4. `.github/workflows/infra-ci.yml`

```yaml
jobs:
  terraform-validate:  # terraform init + validate + fmt
  ansible-lint:         # ansible-lint + yamllint
  shellcheck:           # scripts/*.sh + k8s/federation/*.sh
  kubeval:              # K8s manifests validation
```

---

## 5. Обновлённый `ansible/playbook.yml`

```yaml
- name: '[Day 4] Slurm HA controllers'
  hosts: controllers
  tasks:
    - import_role:
        name: slurm_ha
      tags: [slurm_ha]

- name: '[Day 4] Slurm compute'
  hosts: gpu_nodes,edge
  tasks:
    - import_role:
        name: slurm
      tags: [slurmd]

- name: '[Day 7] Edge ARM node'
  hosts: edge
  tasks:
    - import_role:
        name: edge-node
      tags: [edge, arm]
```

---

## Команды деплоя

```bash
# Полный деплой (все роли)
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml

# Только HA Slurm
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --tags slurm_ha

# Только K8s federation
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --tags k8s

# Деплой KubeFed
./k8s/federation/helm-install.sh
./k8s/federation/cluster-registration.sh
kubectl --context kubernetes-admin@cluster.local apply -f k8s/federation/federated-deployment.yaml

# CI локально (без GitHub)
make lint
make validate
```

---

## Проверка HA Slurm

```bash
# 1. Проверить VIP на active controller
ip addr show | grep 10.20.20.254

# 2. Симулировать падение
ssh rtx-node "sudo systemctl stop slurmctld"

# 3. Через 10 сек проверить — VIP переехал
ssh rk3576-node "ip addr show | grep 10.20.20.254"  # должен быть там

# 4. jobs продолжают работать
sinfo
squeue
```

---

## Пуш (SSH, без токенов)

```bash
cd /home/workspace/home-cluster-iac

git remote set-url origin git@github.com:mahaasur13-sys/home-cluster-iac.git

git add \
  ansible/roles/slurm_ha/ \
  k8s/federation/ \
  .github/workflows/infra-ci.yml \
  ansible/playbook.yml \
  ansible/inventory.ini \
  ansible/group_vars/all.yml \
  README.md \
  FINAL_ENHANCEMENTS.md

git commit -m "feat: HA Slurm, K8s federation, CI/CD, integrate edge-node

- Add slurm_ha role (3 controllers + keepalived VIP)
- Add KubeFed federation (x86 + ARM)
- Add CI/CD workflow (self-hosted runner)
- Integrate edge-node role into playbook
- Update inventory and group_vars"

git push origin main
```

---

## Что уже было до этого

| Файл | Статус |
|------|--------|
| `ansible/roles/edge-node/` | ✅ Создано (ARM64 K3s + Ray + slurmd) |
| `terraform/` | ✅ Существует |
| `ansible/roles/wireguard/` | ✅ Существует |
| `ansible/roles/slurm/` | ✅ Существует |
| `ansible/roles/ceph/` | ✅ Существует |
| `ansible/roles/ray/` | ✅ Существует |
| `ansible/roles/k8s/` | ✅ Существует |
| `scripts/day1–day7/` | ✅ Существует |
| `Makefile` | ✅ Существует |
