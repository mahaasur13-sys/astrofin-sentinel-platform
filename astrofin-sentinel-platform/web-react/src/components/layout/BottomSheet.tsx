import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';

interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
}

export function BottomSheet({ open, onClose, children, title = 'Детали' }: BottomSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && open) {
        onClose();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-label={title} aria-modal="true">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={sheetRef}
        className="fixed inset-x-0 bottom-0 max-h-[85vh] rounded-t-2xl border-t border-gray-700 bg-gray-900 shadow-2xl animate-in slide-in-from-bottom duration-300"
      >
        <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
          <div className="mx-auto h-1 w-10 rounded-full bg-gray-600 md:hidden" />
          <span className="text-sm font-semibold text-gray-300">{title}</span>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:bg-gray-800 hover:text-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            aria-label="Закрыть панель"
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(85vh - 48px)' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
