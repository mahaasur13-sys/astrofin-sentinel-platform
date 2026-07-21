/**
 * BEST PRACTICE EXEMPLAR: Redux Toolkit Slice + AsyncThunk
 * (web-react/src/features/agents/agentsSlice.ts)
 *
 * Why this is an exemplar:
 *
 * 1. TYPED STATE — AgentState interface with discriminated union for status
 *    ('idle' | 'running' | 'success' | 'error'). No stringly-typed state.
 *
 * 2. ACTION CREATORS AS REDUCERS — started/finished/error actions are separate
 *    reducers, not a single reducer with if/else chains.
 *
 * 3. ASYNC THUNK PATTERN — runAgentWithLLM dispatches lifecycle actions
 *    (started → finished/error) inside the thunk, keeping the component
 *    pure (no dispatch calls in JSX).
 *
 * 4. IMMUTABLE UPDATES — createSlice uses Immer under the hood, so we write
 *    "mutable" syntax (state.agents[id].status = 'running') but get immutable
 *    updates automatically.
 *
 * 5. SINGLE SOURCE OF TRUTH — all agent state flows through this slice.
 *    Components only read via useAppSelector, only write via dispatch(thunk).
 */

import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import { createAsyncThunk } from "@reduxjs/toolkit";

// ── Types ─────────────────────────────────────────────────────────────

export type AgentStatus = "idle" | "running" | "success" | "error";

export interface AgentState {
  id: string;
  name: string;
  status: AgentStatus;
  lastResponse?: string;
  lastError?: string;
}

export interface AgentsSliceState {
  agents: Record<string, AgentState>;
  order: string[];
}

// ── Initial State ─────────────────────────────────────────────────────

const initialState: AgentsSliceState = {
  agents: {
    "tech-agent": {
      id: "tech-agent",
      name: "Technical Agent",
      status: "idle",
    },
    "synth-agent": {
      id: "synth-agent",
      name: "Synthesis Agent",
      status: "idle",
    },
    "fund-agent": {
      id: "fund-agent",
      name: "Fundamental Agent",
      status: "idle",
    },
  },
  order: ["tech-agent", "synth-agent", "fund-agent"],
};

// ── Slice ─────────────────────────────────────────────────────────────

const agentsSlice = createSlice({
  name: "agents",
  initialState,
  reducers: {
    agentStarted(state, action: PayloadAction<string>) {
      const id = action.payload;
      if (state.agents[id]) {
        state.agents[id].status = "running";
        state.agents[id].lastError = undefined;
      }
    },
    agentFinished(
      state,
      action: PayloadAction<{ id: string; response: string }>
    ) {
      const { id, response } = action.payload;
      if (state.agents[id]) {
        state.agents[id].status = "success";
        state.agents[id].lastResponse = response;
      }
    },
    agentError(
      state,
      action: PayloadAction<{ id: string; error: string }>
    ) {
      const { id, error } = action.payload;
      if (state.agents[id]) {
        state.agents[id].status = "error";
        state.agents[id].lastError = error;
      }
    },
  },
});

export const { agentStarted, agentFinished, agentError } = agentsSlice.actions;
export default agentsSlice.reducer;
