import { useState, useEffect } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridRowParams } from '@mui/x-data-grid';
import { useDashboardStore } from '@/stores/dashboard.store';
import type { SessionListItem, SessionListResponse } from '@/api/sessionApi';

const columns: GridColDef[] = [
  { field: 'id', headerName: 'Session ID', width: 150 },
  { field: 'timestamp', headerName: 'Time', width: 180, valueFormatter: (value: string) => new Date(value).toLocaleString() },
  { field: 'symbol', headerName: 'Symbol', width: 100 },
  { field: 'signal', headerName: 'Signal', width: 100 },
  { field: 'confidence', headerName: 'Confidence', width: 120, type: 'number', valueFormatter: (value: number) => `${(value * 100).toFixed(1)}%` },
  { field: 'final_pnl', headerName: 'PnL (USDT)', width: 120, type: 'number', valueFormatter: (value: number) => value != null ? `$${value.toFixed(2)}` : 'N/A' },
];

export default function SessionTable() {
  const openContextDrawer = useDashboardStore((s) => s.openContextDrawer);
  const [rows, setRows] = useState<SessionListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch('/api/v1/sessions/?skip=0&limit=50')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: SessionListResponse) => {
        if (!cancelled) setRows(d.items ?? []);
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const handleRowClick = (params: GridRowParams) => {
    openContextDrawer(params.id as string);
  };

  return (
    <div style={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        loading={isLoading}
        onRowClick={handleRowClick}
        sx={{ cursor: 'pointer' }}
      />
    </div>
  );
}
