import { useEffect, useState } from 'react';

interface WindowSize {
  width: number;
  height: number;
}

export function useWindowSize(): WindowSize {
  const [size, setSize] = useState<WindowSize>(() => ({
    width: typeof window !== 'undefined' ? window.innerWidth : 1024,
    height: typeof window !== 'undefined' ? window.innerHeight : 768,
  }));

  useEffect(() => {
    let ticking = false;

    const handleResize = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          setSize({ width: window.innerWidth, height: window.innerHeight });
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('resize', handleResize, { passive: true });
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return size;
}
