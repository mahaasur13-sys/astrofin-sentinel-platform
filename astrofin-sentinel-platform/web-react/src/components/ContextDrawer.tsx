
import { Drawer, Box, Typography, Chip, Stack, Divider, CircularProgress, Button } from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import { closeContextDrawer } from '../store/uiSlice';
import { useGetSessionDetailsQuery } from '../api/sessionApi';

export default function ContextDrawer() {
  const dispatch = useDispatch();
  const { isContextDrawerOpen, selectedSessionId } = useSelector((state: any) => state.ui);
  const { data: details, isLoading } = useGetSessionDetailsQuery(
    selectedSessionId ?? '',
    { skip: !selectedSessionId }
  );

  return (
    <Drawer
      anchor="right"
      open={isContextDrawerOpen}
      onClose={() => dispatch(closeContextDrawer())}
      sx={{ '& .MuiDrawer-paper': { width: { xs: '100%', md: '40%', minWidth: '500px' }, p: 3 } }}
    >
      {isLoading ? (
        <CircularProgress />
      ) : details ? (
        <Box>
          <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
            <Typography variant="h5">
              Session: {details.symbol}
            </Typography>
            <Chip
              label={details.final_signal}
              color={details.final_signal === 'BUY' ? 'success' : details.final_signal === 'SELL' ? 'error' : 'default'}
            />
          </Stack>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>Market Context</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Entry Price: ${details.broker_executed_price?.toFixed(2)} | PnL: {details.final_pnl?.toFixed(2)} USDT
          </Typography>
          <Typography variant="h6" sx={{ mt: 3 }} gutterBottom>Agent Council Debate</Typography>
          <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, mb: 2 }}>
            {details.agent_decisions.map((agent) => (
              <Box key={agent.agent_name} sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  {agent.agent_name} ({agent.signal} | Conf: {agent.confidence})
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {agent.reasoning}
                </Typography>
              </Box>
            ))}
          </Box>
          <Button
            fullWidth
            variant="contained"
            sx={{ mt: 4 }}
            onClick={() => dispatch(closeContextDrawer())}
          >
            Close
          </Button>
        </Box>
      ) : (
        <Typography>No data</Typography>
      )}
    </Drawer>
  );
}
