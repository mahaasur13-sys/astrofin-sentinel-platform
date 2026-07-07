# Ray AI Runtime

## Cluster Layout

```
Ray Head (rtx-node:10.20.20.10)
├── Port 6379: Ray client
├── Port 8265: Dashboard
└── 1× RTX 3060 GPU

└── Ray Workers
    ├── rk3576-edge (10.20.20.20)
    │   └── 1× RK3576 NPU
    └── (future VPS nodes)
```

## Connect to Ray

```python
import ray
ray.init(address="auto")

@ray.remote(num_gpus=1)
def gpu_task():
    import torch
    return torch.cuda.get_device_name(0)

ray.get(gpu_task.remote())
```

## Slurm + Ray Bridge

```bash
# In Slurm job script
source /etc/slurm/rayenv.d/ray.conf
python my_ray_job.py
```

## Ray Dashboard

URL: http://10.20.20.10:8265

Shows: Cluster resources, actors, jobs, logs
