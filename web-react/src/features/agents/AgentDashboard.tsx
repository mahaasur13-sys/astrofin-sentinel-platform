import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { registerAgent, resetAgent, type AgentStatus } from './agentsSlice';
import { runAgentWithLLM } from './agentsThunks';

const TEST_AGENTS = [
  { id: 'technical', name: 'Technical Agent' },
  { id: 'synthesis', name: 'Synthesis Agent' },
  { id: 'quant', name: 'Quant Agent' },
];

function StatusBadge({ status }: { status: AgentStatus }) {
  const colors: Record<AgentStatus, string> = {
    idle: 'bg-slate-500',
    running: 'bg-amber-500 animate-pulse',
    success: 'bg-emerald-500',
    error: 'bg-red-500',
  };
  return (
    <span className={`inline-block w-2.5 h-2.5 rounded-full ${colors[status]}`} />
  );
}

export default function AgentDashboard() {
  const dispatch = useAppDispatch();
  const { items, order } = useAppSelector((s) => s.agents);

  useEffect(() => {
    TEST_AGENTS.forEach((a) => dispatch(registerAgent(a)));
  }, [dispatch]);

  const handleRun = (id: string) => {
    dispatch(runAgentWithLLM({ agentId: id, prompt: `Run analysis for ${id}` }));
  };

  const handleReset = (id: string) => {
    dispatch(resetAgent(id));
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <h1 className="text-3xl font-bold mb-8">AstroFin Sentinel — Agent Dashboard</h1>

      <div className="grid gap-4 max-w-3xl">
        {order.map((id) => {
          const agent = items[id];
          if (!agent) return null;
          const { name, status, lastResponse, lastError } = agent;

          return (
            <div key={id} className="bg-slate-800 rounded-xl p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <StatusBadge status={status} />
                  <span className="font-semibold text-lg">{name}</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleRun(id)}
                    disabled={status === 'running'}
                    className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
                  >
                    Run
                  </button>
                  <button
                    onClick={() => handleReset(id)}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {status === 'success' && lastResponse && (
                <div className="bg-slate-900 rounded-lg p-3 text-sm text-emerald-300 max-h-32 overflow-y-auto">
                  {lastResponse.slice(0, 500)}
                </div>
              )}

              {status === 'error' && lastError && (
                <div className="bg-red-900/40 rounded-lg p-3 text-sm text-red-300">
                  {lastError}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
