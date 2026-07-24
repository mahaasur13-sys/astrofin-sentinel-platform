import type { Meta, StoryObj } from '@storybook/react';
import SafetyGateCard from '../components/sentinel/SafetyGateCard';

const meta: Meta<typeof SafetyGateCard> = {
  title: 'Widgets/SafetyGate',
  component: SafetyGateCard,
  tags: ['autodocs'],
  argTypes: {
    status: { control: 'select', options: ['safe', 'warning', 'danger', 'stopped'] },
    riskPct: { control: 'number', min: 0, max: 10, step: 0.1 },
    maxDrawdown: { control: 'number', min: 0, max: 50, step: 0.5 },
    var95: { control: 'number', min: 0, max: 20, step: 0.5 },
    leverage: { control: 'number', min: 0, max: 25, step: 0.5 },
  },
  decorators: [
    (Story) => (
      <div className="max-w-md rounded-xl border border-gray-800 bg-gray-950 p-4">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof SafetyGateCard>;

export const Safe: Story = {
  args: { status: 'safe', reason: 'All checks passed', riskPct: 2.0, maxDrawdown: 5.2, var95: 1.8, leverage: 1.5 },
  name: 'Safe — Normal Operation',
};

export const Warning: Story = {
  args: { status: 'warning', reason: 'Elevated VIX (>25)', riskPct: 1.0, maxDrawdown: 8.4, var95: 3.2, leverage: 2.0 },
  name: 'Warning — Elevated Risk',
};

export const Danger: Story = {
  args: { status: 'danger', reason: 'Max drawdown limit breached', riskPct: 0.5, maxDrawdown: 12.7, var95: 5.1, leverage: 3.0 },
  name: 'Danger — Risk Limit',
};

export const EmergencyStopped: Story = {
  args: { status: 'stopped', reason: 'Emergency stop by safety gate', riskPct: 0, maxDrawdown: 18.3, var95: 9.5, leverage: 0 },
  name: 'Emergency Stop',
};

export const WithTriggers: Story = {
  args: {
    status: 'warning',
    reason: 'Multiple risk warnings',
    riskPct: 1.0,
    maxDrawdown: 7.1,
    var95: 2.9,
    leverage: 2.5,
    triggers: [
      { time: '2025-07-24T08:12:00Z', reason: 'VIX spike > 30' },
      { time: '2025-07-24T09:45:00Z', reason: 'Correlation break detected' },
    ],
  },
  name: 'With Trigger History',
};
