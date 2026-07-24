import { useState, useCallback, useRef, useEffect } from 'react';

interface UseResizablePanelOptions {
  initialWidth: number;
  minWidth?: number;
  maxWidth?: number;
  direction?: 'left' | 'right';
  storageKey?: string;
}

function readStorage(key: string): string | null {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return localStorage.getItem(key);
    }
  } catch {
    // localStorage blocked or unavailable
  }
  return null;
}

function writeStorage(key: string, value: string): void {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(key, value);
    }
  } catch {
    // localStorage blocked
  }
}

export function useResizablePanel({
  initialWidth,
  minWidth = 180,
  maxWidth = 500,
  direction = 'left',
  storageKey,
}: UseResizablePanelOptions) {
  const savedWidth = storageKey ? readStorage(storageKey) : null;

  const [width, setWidth] = useState(
    savedWidth ? parseInt(savedWidth, 10) : initialWidth
  );
  const [isResizing, setIsResizing] = useState(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsResizing(true);
      startXRef.current = e.clientX;
      startWidthRef.current = width;

      try {
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
      } catch {
        // document.body may not be available
      }
    },
    [width]
  );

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const delta =
        direction === 'left'
          ? e.clientX - startXRef.current
          : startXRef.current - e.clientX;

      const newWidth = Math.max(
        minWidth,
        Math.min(maxWidth, startWidthRef.current + delta)
      );
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      try {
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      } catch {
        // ignore
      }

      if (storageKey) {
        writeStorage(storageKey, width.toString());
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, direction, minWidth, maxWidth, storageKey, width]);

  const toggle = useCallback(
    (collapsedWidth: number = 56) => {
      const newWidth = width <= collapsedWidth + 10 ? initialWidth : collapsedWidth;
      setWidth(newWidth);
      if (storageKey) {
        writeStorage(storageKey, newWidth.toString());
      }
    },
    [width, initialWidth, storageKey]
  );

  return { width, isResizing, handleMouseDown, toggle };
}
