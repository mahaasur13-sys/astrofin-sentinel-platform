import { createAsyncThunk } from '@reduxjs/toolkit';
import { agentStarted, agentFinished, agentError } from './agentsSlice';

const API_URL = 'http://localhost:8000/api/v1/agent/run';

export const runAgentWithLLM = createAsyncThunk(
  'agents/runWithLLM',
  async ({ agentId, prompt }: { agentId: string; prompt: string }, { dispatch }) => {
    dispatch(agentStarted(agentId));
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId, prompt }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      dispatch(agentFinished({ id: agentId, response: data.result }));
      return data.result;
    } catch (err: any) {
      const msg = err.message || 'Unknown error';
      dispatch(agentError({ id: agentId, error: msg }));
      throw err;
    }
  },
);
