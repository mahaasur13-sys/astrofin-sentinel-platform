# Architecture - ATOM Federation OS

## Overview

ATOM Federation OS is a deterministic federation runtime.

## Components

- v10.0 Core: DeterministicClock, GlobalExecutionBarrier
- Persistence: EventStore, WAL, MutationLedger
- Observability: TraceLedger, ReplayCertifier
- K8s: DeterministicPodScheduler, DeterministicOperator
- PBFT: federation/byzantine, consensus_resolver

See: `CONTROL_LOOP_ARCHITECTURE.md`, `AGENTS.md`.