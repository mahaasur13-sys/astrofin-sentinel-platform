import { configureStore } from '@reduxjs/toolkit';
import agentsReducer from '../features/agents/agentsSlice';
import llmReducer from '../features/llm/llmSlice';

export const store = configureStore({
  reducer: {
    agents: agentsReducer,
    llm: llmReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
