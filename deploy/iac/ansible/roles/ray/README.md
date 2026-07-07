# Role: ray

Deploys Ray AI runtime (head + workers).

## Architecture

- Ray head on RTX 3060 node (GPU)
- Ray workers on RK3576 edge node (CPU)

## Test

```bash
ray status            # on head
ray exec clustername "ray status"  # remote
```
