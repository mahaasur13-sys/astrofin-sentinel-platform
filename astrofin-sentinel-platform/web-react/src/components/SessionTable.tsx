import * as React from 'react';
import { DataGrid, GridColDef, GridRowParams } from '@mui/x-data-grid';
import { useDispatch } from 'react-redux';
import { openContextDrawer } from '../store/uiSlice';

interface SessionRow {
  id: string;
  timestamp: string;
  symbol: string;
  signal: string;
  confidence: number;
  final_pnl: number;
}

const columns: GridColDef[] = [
  { field: 'id', headerName: 'Session ID', width: 150 },
  { field: 'timestamp', headerName: 'Time', width: 180 },
  { field: 'symbol', headerName: 'Symbol', width: 100 },
  { field: 'signal', headerName: 'Signal', width: 100 },
  { field: 'confidence', headerName: 'Confidence', width: 120, type: 'number' },
  { field: 'final_pnl', headerName: 'PnL (USDT)', width: 120, type: 'number' },
];

export default function SessionTable({ rows }: { rows: SessionRow[] }) {
  const dispatch = useDispatch();

  const handleRowClick = (params: GridRowParams) => {
    dispatch(openContextDrawer(params.id as string));
  };

  return (
    <div style={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        onRowClick={handleRowClick}
        sx={{ cursor: 'pointer' }}
      />
    </div>
  );
}
