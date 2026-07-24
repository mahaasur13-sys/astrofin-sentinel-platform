import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  isContextDrawerOpen: boolean;
  selectedSessionId: string | null;
}

const initialState: UIState = {
  isContextDrawerOpen: false,
  selectedSessionId: null,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    openContextDrawer: (state, action: PayloadAction<string>) => {
      state.selectedSessionId = action.payload;
      state.isContextDrawerOpen = true;
    },
    closeContextDrawer: (state) => {
      state.isContextDrawerOpen = false;
      state.selectedSessionId = null;
    },
  },
});

export const { openContextDrawer, closeContextDrawer } = uiSlice.actions;
export default uiSlice.reducer;
