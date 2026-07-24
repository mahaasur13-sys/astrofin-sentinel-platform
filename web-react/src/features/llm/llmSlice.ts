import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from '@reduxjs/toolkit';

export type LLMPreference = 'cost' | 'quality' | 'latency';

interface ActiveSession {
  model: string;
  lastUsed: number;
}

interface LLMState {
  preference: LLMPreference;
  activeSessions: Record<string, ActiveSession>;
}

const initialState: LLMState = {
  preference: 'cost',
  activeSessions: {},
};

const llmSlice = createSlice({
  name: 'llm',
  initialState,
  reducers: {
    setPreference(state, action: PayloadAction<LLMPreference>) {
      state.preference = action.payload;
    },
    sessionStarted(state, action: PayloadAction<{ sessionId: string; model: string }>) {
      const { sessionId, model } = action.payload;
      state.activeSessions[sessionId] = { model, lastUsed: Date.now() };
    },
    sessionUsed(state, action: PayloadAction<string>) {
      const s = state.activeSessions[action.payload];
      if (s) s.lastUsed = Date.now();
    },
    evictStaleSessions(state, action: PayloadAction<number>) {
      const ttl = action.payload || 300_000;
      const now = Date.now();
      for (const [id, s] of Object.entries(state.activeSessions)) {
        if (now - s.lastUsed > ttl) {
          delete state.activeSessions[id];
        }
      }
    },
  },
});

export const {
  setPreference,
  sessionStarted,
  sessionUsed,
  evictStaleSessions,
} = llmSlice.actions;

export default llmSlice.reducer;
