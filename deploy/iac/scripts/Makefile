.PHONY: day1 day2 day3 day4 day5 day6 day7 all verify infra-ci

INVENTORY := ../ansible/inventory.ini
TERRAFORM_DIR := ../terraform/mikrotik

# Default target
all: day1 day2 day3 day4 day5 day6 day7

# Day 1: Network foundation — AmneziaWG mesh + MikroTik VLAN
day1:
	@echo "Running Day 1: Network foundation..."
	./day1_network.sh

# Day 2: Base OS — Docker, Python, NTP, SSH, chrony, UFW
day2:
	@echo "Running Day 2: Base OS setup..."
	./day2_base.sh

# Day 3: Compute — CUDA drivers, nvidia-container-runtime, ML Python
day3:
	@echo "Running Day 3: Compute node preparation..."
	./day3_compute.sh

# Day 4: Slurm GPU cluster — slurmctld + slurmd + GPU partition
day4:
	@echo "Running Day 4: Slurm GPU cluster..."
	./day4_slurm.sh

# Day 5: Ray AI cluster — head on GPU node, workers on ARM
day5:
	@echo "Running Day 5: Ray AI cluster..."
	./day5_ray.sh

# Day 6: Ceph storage + Monitoring (Prometheus + Grafana)
day6:
	@echo "Running Day 6: Ceph storage + Monitoring stack..."
	./day6_ceph.sh
	./day6_monitoring.sh

# Day 7: Full integration — job routing + storage + Slurm-Ray bridge
day7:
	@echo "Running Day 7: Integration layer..."
	./day7_integration.sh

# Terraform (MikroTik)
infra-plan:
	@echo "Running Terraform plan for MikroTik..."
	cd $(TERRAFORM_DIR) && terraform init -upgrade && terraform validate && terraform plan

infra-apply:
	@echo "Applying Terraform for MikroTik (requires secrets)..."
	cd $(TERRAFORM_DIR) && terraform apply

infra-destroy:
	@echo "Destroying Terraform resources..."
	cd $(TERRAFORM_DIR) && terraform destroy

# Verification targets
verify:
	@echo "=== Cluster Verification ==="
	ansible all -i $(INVENTORY) -m ping
	@echo "--- WireGuard status ---"
	ansible all -i $(INVENTORY) -m shell -a "wg show wg0 | head -5" 2>/dev/null || echo "wg0 not configured yet"
	@echo "--- Slurm partitions ---"
	ansible all -i $(INVENTORY) -m shell -a "sinfo -- partitions" 2>/dev/null || echo "Slurm not configured yet"
	@echo "--- Ceph status ---"
	ansible all -i $(INVENTORY) -m shell -a "ceph -s 2>/dev/null" 2>/dev/null || echo "Ceph not configured yet"
	@echo "--- Ray status ---"
	ansible all -i $(INVENTORY) -m shell -a "ray status 2>/dev/null" 2>/dev/null || echo "Ray not configured yet"

verify-docker:
	ansible all -i $(INVENTORY) -m shell -a "docker --version && docker ps"

verify-gpu:
	ansible gpu-node -i $(INVENTORY) -m shell -a "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"

# Ansible lint
lint:
	ansible-lint -c .ansible-lint.yml site.yml

# Terraform fmt
tf-fmt:
	cd $(TERRAFORM_DIR) && terraform fmt -recursive
