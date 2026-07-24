import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: 'left' | 'right';
  label?: string;
}

export function MobileDrawer({
  open,
  onClose,
  children,
  side = 'left',
  label = 'Menu',
}: MobileDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  useEffect(() => {
    if (open) {
      drawerRef.current?.focus();
    }
  }, [open]);

  if (!open) return null;

  const slideClass =
    side === 'left'
      ? 'left-0 -translate-x-full data-[open]:translate-x-0'
      : 'right-0 translate-x-full data-[open]:translate-x-0';

  return (
    <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label={label}>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={drawerRef}
        data-open={open}
        className={`fixed top-0 ${slideClass} h-full w-[min(320px,85vw)] bg-[#0d0d14] shadow-2xl transition-transform duration-300 ease-in-out focus:outline-none`}
        tabIndex={-1}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <span className="text-sm font-semibold text-gray-300">{label}</span>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
            aria-label="Close drawer"
          >
            <X className="size-5" />
          </button>
        </div>
        <div className="h-[calc(100%-49px)] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
