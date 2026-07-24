import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { VirtualAgentGrid } from '../VirtualAgentGrid';

const agent = (i: number) => ({
  id: `agent-${i}`,
  name: `AlphaAgent-${i}`,
  weight: 0.2,
  signal: 'buy' as const,
  confidence: 0.85,
  winRate: 65,
  sharpe: 1.4,
  pnl: 8.0,
  status: 'active' as const,
  lastRun: new Date().toISOString(),
});

describe('VirtualAgentGrid', () => {
  it('renders the scrollable container with agents', () => {
    const agents = Array.from({ length: 3 }, (_, i) => agent(i));
    const { container } = render(<VirtualAgentGrid agents={agents} />);
    expect(container.querySelector('[class*="overflow-auto"]')).toBeInTheDocument();
  });

  it('handles empty agents array', () => {
    const { container } = render(<VirtualAgentGrid agents={[]} />);
    expect(container.querySelector('[class*="overflow-auto"]')).toBeInTheDocument();
  });

  it('does not render Run button when onRunAgent is not provided', () => {
    const { container } = render(<VirtualAgentGrid agents={[agent(0)]} />);
    expect(container.querySelector('button')).not.toBeInTheDocument();
  });
});
