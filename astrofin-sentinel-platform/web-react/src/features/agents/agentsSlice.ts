import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from '@reduxjs/toolkit';

export type AgentStatus = 'idle' | 'running' | 'success' | 'error';

export interface AgentEntry {
  id: string;
  name: string;
  status: AgentStatus;
  lastResponse: string | null;
  lastError: string | null;
}

interface AgentsState {
  items: Record<string, AgentEntry>;
  order: string[];
}

const initialState: AgentsState = {
  items: {},
  order: [],
};

const agentsSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    registerAgent(state, action: PayloadAction<{ id: string; name: string }>) {
      const { id, name } = action.payload;
      if (!state.items[id]) {
        state.items[id] = {
          id, name,
          status: 'idle',
          lastResponse: null,
          lastError: null,
        };
        state.order.push(id);
      }
    },
    agentStarted(state, action: PayloadAction<string>) {
      const agent = state.items[action.payload];
      if (agent) {
        agent.status = 'running';
        agent.lastError = null;
      }
    },
    agentFinished(state, action: PayloadAction<{ id: string; response: string }>) {
      const agent = state.items[action.payload.id];
      if (agent) {
        agent.status = 'success';
        agent.lastResponse = action.payload.response;
      }
    },
    agentError(state, action: PayloadAction<{ id: string; error: string }>) {
      const agent = state.items[action.payload.id];
      if (agent) {
        agent.status = 'error';
        agent.lastError = action.payload.error;
      }
    },
    resetAgent(state, action: PayloadAction<string>) {
      const agent = state.items[action.payload];
      if (agent) {
        agent.status = 'idle';
        agent.lastResponse = null;
        agent.lastError = null;
      }
    },
  },
});

export const {
  registerAgent,
  agentStarted,
  agentFinished,
  agentError,
  resetAgent,
} = agentsSlice.actions;

export default agentsSlice.reducer;
