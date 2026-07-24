import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import AstroMindChat from '../AstroMindChat';
import { useDashboardStore, initialState } from '@/stores/dashboard.store';

describe('AstroMindChat', () => {
  beforeEach(() => {
    useDashboardStore.getState().reset();
  });

  it('renders embedded variant', () => {
    render(<AstroMindChat variant="embedded" />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders floating variant', () => {
    render(<AstroMindChat variant="floating" />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders input area', () => {
    render(<AstroMindChat />);
    expect(screen.getByPlaceholderText(/13 агенто/i)).toBeInTheDocument();
  });

  it('renders quick action buttons', () => {
    render(<AstroMindChat />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it('applies className when provided', () => {
    const { container } = render(<AstroMindChat className="test-class" />);
    expect(container.firstChild).toHaveClass('test-class');
  });
});
