import type { Meta, StoryObj } from '@storybook/react';
import AgentPerformanceGrid from '../components/sentinel/AgentPerformanceGrid';

const meta: Meta<typeof AgentPerformanceGrid> = {
  title: 'Widgets/AgentPerformanceGrid',
  component: AgentPerformanceGrid,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div className="max-w-5xl rounded-xl border border-gray-800 bg-gray-950 p-4">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof AgentPerformanceGrid>;

const sampleAgents = [
  { id: 'fundamental', name: 'Fundamental', weight: 20, signal: 'strong_buy' as const, confidence: 85, winRate: 72, sharpe: 1.8, pnl: 12500, status: 'active' as const, lastRun: '2025-07-24T08:00:00Z' },
  { id: 'quant', name: 'Quant', weight: 20, signal: 'buy' as const, confidence: 78, winRate: 68, sharpe: 1.5, pnl: 9800, status: 'active' as const, lastRun: '2025-07-24T07:55:00Z' },
  { id: 'macro', name: 'Macro', weight: 15, signal: 'hold' as const, confidence: 55, winRate: 61, sharpe: 0.9, pnl: 3200, status: 'idle' as const, lastRun: '2025-07-24T07:50:00Z' },
  { id: 'options', name: 'Options Flow', weight: 15, signal: 'sell' as const, confidence: 62, winRate: 59, sharpe: 0.7, pnl: -1500, status: 'active' as const, lastRun: '2025-07-24T07:45:00Z' },
  { id: 'sentiment', name: 'Sentiment', weight: 10, signal: 'buy' as const, confidence: 71, winRate: 55, sharpe: 0.5, pnl: 4500, status: 'error' as const, lastRun: '2025-07-24T07:30:00Z' },
  { id: 'bradley', name: 'Bradley', weight: 5, signal: 'hold' as const, confidence: 45, winRate: 48, sharpe: 0.2, pnl: -800, status: 'idle' as const, lastRun: '2025-07-24T07:20:00Z' },
  { id: 'cycle', name: 'Cycle', weight: 5, signal: 'strong_sell' as const, confidence: 66, winRate: 52, sharpe: 0.4, pnl: 1200, status: 'active' as const, lastRun: '2025-07-24T07:15:00Z' },
];

export const FullBoard: Story = {
  args: { agents: sampleAgents },
  name: 'Full Agent Board (7 agents)',
};

export const FewAgents: Story = {
  args: { agents: sampleAgents.slice(0, 3) },
  name: 'Few Agents (3)',
};

export const EmptyBoard: Story = {
  args: { agents: [] },
  name: 'Empty Board',
};
