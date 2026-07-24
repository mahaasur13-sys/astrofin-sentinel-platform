import { type ReactNode, useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: 'left' | 'right';
  title?: string;
}

export function MobileDrawer({
  open,
  onClose,
  children,
  side = 'left',
  title,
}: MobileDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  const positionClasses =
    side === 'left'
      ? 'left-0 border-r'
      : 'right-0 border-l';

  return (
    <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={drawerRef}
        className={`absolute top-0 bottom-0 w-72 max-w-[85vw] border-border bg-background shadow-2xl ${positionClasses} animate-slide-in`}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          {title && <span className="text-sm font-semibold text-foreground">{title}</span>}
          <button
            onClick={onClose}
            className="ml-auto rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted"
            aria-label="Закрыть меню"
          >
            <X className="size-5" />
          </button>
        </div>
        <div className="overflow-y-auto p-4">{children}</div>
      </div>
    </div>
  );
}
