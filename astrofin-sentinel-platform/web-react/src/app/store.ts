import { configureStore } from '@reduxjs/toolkit';
import agentsReducer from '../features/agents/agentsSlice';
import llmReducer from '../features/llm/llmSlice';
import uiReducer from '../store/uiSlice';
import { sessionApi } from '../api/sessionApi';

export const store = configureStore({
  reducer: {
    agents: agentsReducer,
    llm: llmReducer,
    ui: uiReducer,
    [sessionApi.reducerPath]: sessionApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(sessionApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
