import type { Meta, StoryObj } from '@storybook/react';
import { RegimeRadar, type Regime, type RegimeRadarProps } from '../components/sentinel/RegimeRadar';

const meta: Meta<typeof RegimeRadar> = {
  title: 'Widgets/RegimeRadar',
  component: RegimeRadar,
  tags: ['autodocs'],
  argTypes: {
    currentRegime: {
      control: 'select',
      options: ['bull', 'bear', 'sideways', 'high_vol', 'anomaly'],
    },
    compact: { control: 'boolean' },
  },
  decorators: [
    (Story) => (
      <div className="max-w-sm rounded-xl border border-gray-800 bg-gray-950 p-4">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof RegimeRadar>;

export const BullMarket: Story = {
  args: {
    currentRegime: 'bull',
    probabilities: { bull: 0.55, bear: 0.10, sideways: 0.20, high_vol: 0.08, anomaly: 0.07 },
  },
  name: 'Bull Market Regime',
};

export const HighVolatility: Story = {
  args: {
    currentRegime: 'high_vol',
    probabilities: { bull: 0.15, bear: 0.25, sideways: 0.10, high_vol: 0.45, anomaly: 0.05 },
  },
  name: 'High Volatility',
};

export const AnomalyDetected: Story = {
  args: {
    currentRegime: 'anomaly',
    probabilities: { bull: 0.02, bear: 0.03, sideways: 0.02, high_vol: 0.08, anomaly: 0.85 },
  },
  name: 'Market Anomaly',
};

export const CompactMode: Story = {
  args: {
    currentRegime: 'sideways',
    probabilities: { bull: 0.20, bear: 0.15, sideways: 0.50, high_vol: 0.10, anomaly: 0.05 },
    compact: true,
  },
  name: 'Compact View',
};
