'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface UseResizablePanelOptions {
  initialWidth: number;
  minWidth?: number;
  maxWidth?: number;
  direction?: 'left' | 'right';
  storageKey?: string;
}

export function useResizablePanel({
  initialWidth,
  minWidth = 180,
  maxWidth = 500,
  direction = 'left',
  storageKey,
}: UseResizablePanelOptions) {
  const savedWidth =
    typeof window !== 'undefined' && storageKey
      ? localStorage.getItem(storageKey)
      : null;

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

      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
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
      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      if (storageKey) {
        localStorage.setItem(storageKey, width.toString());
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
        localStorage.setItem(storageKey, newWidth.toString());
      }
    },
    [width, initialWidth, storageKey]
  );

  return { width, isResizing, handleMouseDown, toggle };
}
