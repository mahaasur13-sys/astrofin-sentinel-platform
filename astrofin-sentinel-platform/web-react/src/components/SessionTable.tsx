import * as React from 'react';
import { DataGrid, GridColDef, GridRowParams } from '@mui/x-data-grid';
import { useDispatch } from 'react-redux';
import { openContextDrawer } from '../store/uiSlice';
import { useGetSessionsListQuery } from '../api/sessionApi';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'Session ID', width: 150 },
  { field: 'timestamp', headerName: 'Time', width: 180, valueFormatter: (value: string) => new Date(value).toLocaleString() },
  { field: 'symbol', headerName: 'Symbol', width: 100 },
  { field: 'signal', headerName: 'Signal', width: 100 },
  { field: 'confidence', headerName: 'Confidence', width: 120, type: 'number', valueFormatter: (value: number) => `${(value * 100).toFixed(1)}%` },
  { field: 'final_pnl', headerName: 'PnL (USDT)', width: 120, type: 'number', valueFormatter: (value: number) => value != null ? `$${value.toFixed(2)}` : 'N/A' },
];

export default function SessionTable() {
  const dispatch = useDispatch();
  const { data, isLoading } = useGetSessionsListQuery({ skip: 0, limit: 50 });

  const handleRowClick = (params: GridRowParams) => {
    dispatch(openContextDrawer(params.id as string));
  };

  return (
    <div style={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={data?.items || []}
        columns={columns}
        loading={isLoading}
        onRowClick={handleRowClick}
        sx={{ cursor: 'pointer' }}
      />
    </div>
  );
}
