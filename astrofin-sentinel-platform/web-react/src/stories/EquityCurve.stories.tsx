import type { Meta, StoryObj } from '@storybook/react';
import EquityCurve from '../components/sentinel/EquityCurve';

const meta: Meta<typeof EquityCurve> = {
  title: 'Widgets/EquityCurve',
  component: EquityCurve,
  tags: ['autodocs'],
  argTypes: {
    height: { control: 'number', defaultValue: 260 },
  },
  decorators: [
    (Story) => (
      <div className="w-full max-w-4xl rounded-xl border border-gray-800 bg-gray-950 p-4">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof EquityCurve>;

const generateEquityData = (days: number, startEquity: number, trend: number) => {
  const regimes = ['bull', 'bear', 'sideways', 'high_vol', 'anomaly'] as const;
  let equity = startEquity;
  return Array.from({ length: days }, (_, i) => {
    equity = equity * (1 + trend + (Math.random() - 0.45) * 0.03);
    return {
      date: new Date(2025, 0, i + 1).toISOString().slice(0, 10),
      equity: Math.round(equity),
      regime: regimes[Math.floor(i / (days / regimes.length))],
    };
  });
};

export const Bullish: Story = {
  args: {
    data: generateEquityData(90, 10000, 0.005),
    height: 260,
  },
  name: 'Bullish Trend (90 days)',
};

export const Bearish: Story = {
  args: {
    data: generateEquityData(90, 10000, -0.004),
    height: 260,
  },
  name: 'Bearish Drawdown (90 days)',
};

export const LongTerm: Story = {
  args: {
    data: generateEquityData(365, 10000, 0.002),
    height: 320,
  },
  name: 'Long-Term (365 days)',
};

export const FewDataPoints: Story = {
  args: {
    data: generateEquityData(5, 10000, 0.01),
    height: 260,
  },
  name: 'Few Data Points (edge case)',
};

export const Empty: Story = {
  args: {
    data: [],
    height: 260,
  },
  name: 'Empty Dataset',
};
