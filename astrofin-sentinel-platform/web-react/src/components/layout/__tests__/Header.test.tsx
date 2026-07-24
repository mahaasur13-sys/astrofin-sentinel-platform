import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Header } from '../Header';
import { useDashboardStore } from '@/stores/dashboard.store';

const defaultProps = {
  connectionStatus: 'connected' as const,
  latencyMs: 42,
  activeView: 'overview',
  isMobile: false,
  onMenuToggle: () => {},
};

describe('Header', () => {
  beforeEach(() => {
    useDashboardStore.getState().reset();
  });

  it('renders the brand name', () => {
    render(<Header {...defaultProps} />);
    expect(screen.getByText('AstroFin')).toBeInTheDocument();
  });

  it('displays connection status', () => {
    render(<Header {...defaultProps} />);
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  it('shows latency when connected', () => {
    render(<Header {...defaultProps} />);
    expect(screen.getByText(/42/)).toBeInTheDocument();
  });

  it('hides latency when disconnected', () => {
    render(<Header {...defaultProps} connectionStatus="disconnected" latencyMs={0} />);
    expect(screen.queryByText(/ms/)).not.toBeInTheDocument();
  });

  it('displays active view label as text', () => {
    render(<Header {...defaultProps} activeView="agents" />);
    expect(screen.getByText('agents')).toBeInTheDocument();
  });

  it('renders hamburger on mobile', () => {
    render(<Header {...defaultProps} isMobile={true} />);
    expect(screen.getByLabelText(/Toggle navigation menu/i)).toBeInTheDocument();
  });

  it('renders sidebar toggle on desktop', () => {
    render(<Header {...defaultProps} isMobile={false} />);
    expect(screen.getByLabelText(/sidebar/)).toBeInTheDocument();
  });
});
