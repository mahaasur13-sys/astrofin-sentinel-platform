# AstroFin Sentinel V5 Architecture

```mermaid
graph TD
    Web[Flask/Dash] --> Orchestrator[Orchestration]
    Orchestrator --> Router[Intent Router]
    Router --> Thompson[Thompson Sampling]
    Thompson --> Agents[Agent Pools]
    Agents --> Technical[Technical]
    Agents --> Macro[Macro]
    Agents --> Astro[Astro Council]
    Agents --> Electoral[Electoral]
    Agents --> Synthesis[Synthesis Agent]
    Synthesis --> Decision[Final Signal]
    Data[Market Data] --> Agents
    Cache[Redis Cache] --> Agents
    DB[(TimescaleDB)] --> Backtest
    Prometheus --> Monitoring
    Grafana --> Monitoring
