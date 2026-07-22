package contracts

type RouteDecision struct {
	AgentID   string
	Score     float64
	Reason    string
	Tick      uint64
}

type ReflectionResult struct {
	AgentID    string
	Success    bool
	Quality    float64
	Outcome    string
	Confidence float64
}
