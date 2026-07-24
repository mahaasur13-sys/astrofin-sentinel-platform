import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Sidebar } from '../Sidebar';
import { useDashboardStore } from '@/stores/dashboard.store';

describe('Sidebar', () => {
  beforeEach(() => {
    useDashboardStore.getState().reset();
  });

  it('renders navigation heading', () => {
    render(<Sidebar />);
    expect(screen.getByText('Navigation')).toBeInTheDocument();
  });

  it('renders system status', () => {
    render(<Sidebar />);
    expect(screen.getByText('System online')).toBeInTheDocument();
  });

  it('renders all navigation items as buttons', () => {
    render(<Sidebar />);
    const nav = screen.getByLabelText('Main navigation');
    expect(nav).toBeInTheDocument();
    const buttons = nav.querySelectorAll('button');
    expect(buttons.length).toBeGreaterThanOrEqual(5);
  });

  it('highlights the active view with aria-current', () => {
    useDashboardStore.setState({ activeView: 'agents' });
    render(<Sidebar />);
    expect(screen.getByRole('button', { name: /Agents/ })).toHaveAttribute('aria-current', 'page');
  });

  it('renders in drawer mode when isOpen is set', () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />);
    expect(screen.getByLabelText('Close navigation menu')).toBeInTheDocument();
  });

  it('hides close button when not in drawer mode', () => {
    render(<Sidebar />);
    expect(screen.queryByLabelText('Close navigation menu')).not.toBeInTheDocument();
  });
});
