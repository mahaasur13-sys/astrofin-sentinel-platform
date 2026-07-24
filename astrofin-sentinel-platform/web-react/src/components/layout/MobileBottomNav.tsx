import { LayoutDashboard, Activity, Users, Radio, BrainCircuit, TrendingUp, Settings } from 'lucide-react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Обзор', icon: <LayoutDashboard className="size-5" /> },
  { id: 'agents', label: 'Агенты', icon: <Users className="size-5" /> },
  { id: 'radar', label: 'Радар', icon: <Radio className="size-5" /> },
  { id: 'sessions', label: 'Сессии', icon: <Activity className="size-5" /> },
  { id: 'astro', label: 'Astro', icon: <BrainCircuit className="size-5" /> },
  { id: 'pnl', label: 'P&L', icon: <TrendingUp className="size-5" /> },
  { id: 'settings', label: 'Настр', icon: <Settings className="size-5" /> },
];

interface MobileBottomNavProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export function MobileBottomNav({ activeView, onViewChange }: MobileBottomNavProps) {
  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-30 border-t border-gray-800 bg-gray-950/95 backdrop-blur-sm lg:hidden"
      aria-label="Мобильная навигация"
    >
      <div className="flex items-center justify-around px-1 py-1 safe-area-bottom">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`flex flex-col items-center gap-0.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${
                isActive
                  ? 'text-blue-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
            >
              {item.icon}
              <span className="truncate max-w-[64px]">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
