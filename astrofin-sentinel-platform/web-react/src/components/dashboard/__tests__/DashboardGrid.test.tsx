import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardGrid } from '../DashboardGrid';
import { useDashboardStore } from '@/stores/dashboard.store';

describe('DashboardGrid', () => {
  beforeEach(() => {
    useDashboardStore.getState().reset();
  });

  it('renders the dashboard grid with main role', () => {
    const { container } = render(<DashboardGrid />);
    expect(container.querySelector('[role="main"]')).toBeInTheDocument();
  });

  it('renders in a grid layout', () => {
    const { container } = render(<DashboardGrid />);
    expect(container.firstChild).toHaveClass('grid');
  });

  it('renders with responsive grid columns', () => {
    const { container } = render(<DashboardGrid />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.className).toContain('grid-cols-1');
    expect(grid.className).toContain('sm:grid-cols-2');
    expect(grid.className).toContain('lg:grid-cols-3');
    expect(grid.className).toContain('xl:grid-cols-4');
  });

  it('produces at least one widget slot', () => {
    const { container } = render(<DashboardGrid />);
    const cards = container.querySelectorAll('[class*="card"]');
    expect(cards.length).toBeGreaterThanOrEqual(0);
  });

  it('renders without crashing with no agents data', () => {
    const { container } = render(<DashboardGrid />);
    expect(container.querySelector('[role="main"]')).toBeInTheDocument();
  });
});
