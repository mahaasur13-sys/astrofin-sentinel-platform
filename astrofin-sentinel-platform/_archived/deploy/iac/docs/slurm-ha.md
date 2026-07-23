# Slurm HA Setup

## Architecture

```
┌─────────────────────────────────────────┐
│       Slurm Controller (Primary)         │
│            rtx-node                       │
│         10.20.20.10 :6817                │
└─────────────────┬───────────────────────┘
                  │ MUNGE auth
      ┌───────────┼───────────┐
      │           │           │
┌─────▼───┐  ┌────▼────┐  ┌──▼────┐
│ slurmd  │  │ slurmd  │  │ slurmd│
│rtx-node│  │rk3576-edge│ │ VPS  │
│GPU:RTX3060│ │CPU only │  │(future)│
└─────────┘  └─────────┘  └───────┘
```

## GPU Partition

| Setting | Value |
|---------|-------|
| Partition | gpu |
| Default node | rtx-node |
| MaxTime | INFINITE |
| State | UP |
| GRES | gpu:rtx3060:1 |

## HA Controller Setup (3 controllers)

1. **Primary**: rtx-node (10.20.20.10)
2. **Backup 1**: rk3576-edge (10.20.20.20) 
3. **Backup 2**: VPS (optional)

## Useful Commands

```bash
# Check cluster
sinfo

# Check nodes
scontrol show nodes

# Check jobs
squeue

# Submit GPU job
srun --partition=gpu --gres=gpu:rtx3060:1 nvidia-smi

# Submit batch job
sbatch --partition=gpu --gres=gpu:rtx3060:1 --wrap="python train.py"
```
