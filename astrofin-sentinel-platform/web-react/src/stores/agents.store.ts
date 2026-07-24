import { create } from 'zustand';
import type { AgentDetail } from '@/types';

interface AgentsState {
  details: Record<string, AgentDetail>;
  selectedAgentId: string | null;

  setAgentDetails: (details: Record<string, AgentDetail>) => void;
  selectAgent: (id: string | null) => void;
}

export const useAgentsStore = create<AgentsState>()((set) => ({
  details: {},
  selectedAgentId: null,

  setAgentDetails: (details) => set({ details }),
  selectAgent: (id) => set({ selectedAgentId: id }),
}));
