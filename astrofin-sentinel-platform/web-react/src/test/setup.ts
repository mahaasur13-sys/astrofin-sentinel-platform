import '@testing-library/jest-dom/vitest';

// jsdom polyfill for scrollIntoView (used by AstroMindChat)
Element.prototype.scrollIntoView = () => {};

// Reset Zustand stores between tests
// Imported lazily to avoid circular deps
declare global { var __resetZustandStores: (() => void) | undefined; }
