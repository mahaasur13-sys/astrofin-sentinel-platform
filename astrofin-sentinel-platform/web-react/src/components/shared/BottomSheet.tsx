import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  label?: string;
  height?: string;
}

export function BottomSheet({
  open,
  onClose,
  children,
  label = 'Panel',
  height = '70vh',
}: BottomSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null);

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
      sheetRef.current?.focus();
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label={label}>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        ref={sheetRef}
        className={`fixed bottom-0 left-0 right-0 rounded-t-2xl bg-[#0d0d14] shadow-2xl transition-transform duration-300 ease-in-out ${
          open ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ maxHeight: height }}
        tabIndex={-1}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <div className="mx-auto mb-0.5 h-1 w-10 rounded-full bg-white/20" />
          <span className="absolute left-4 text-sm font-semibold text-gray-300">{label}</span>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
            aria-label="Close panel"
          >
            <X className="size-5" />
          </button>
        </div>
        <div className="overflow-y-auto px-2 pb-6" style={{ maxHeight: `calc(${height} - 49px)` }}>
          {children}
        </div>
      </div>
    </div>
  );
}
