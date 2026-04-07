import { Bell, ChevronDown, Activity, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Shift } from '../../types';

interface AppShellProps {
  children: React.ReactNode;
  currentUser?: string;
  currentShift?: Shift;
  siteName?: string;
}

const shiftLabels: Record<Shift, string> = {
  morning: 'Morning shift',
  afternoon: 'Afternoon shift',
  night: 'Night shift',
};

export default function AppShell({
  children,
  currentUser = 'Maya R.',
  currentShift = 'morning',
  siteName = 'Rockville Site A',
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Top Bar */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 h-14">
          {/* Left: Logo */}
          <Link to="/" className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-primary" />
            <span className="text-lg font-semibold text-primary">BioFlow</span>
          </Link>

          {/* Center-right: Context */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <span className="font-medium text-neutral-700">{siteName}</span>
              <span className="text-neutral-300">·</span>
              <span>{shiftLabels[currentShift]}</span>
              <span className="text-neutral-300">·</span>
              <span>{currentUser}</span>
            </div>

            {/* Notification bell */}
            <button className="relative p-2 rounded-lg hover:bg-neutral-100 transition-colors">
              <Bell className="w-5 h-5 text-neutral-500" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full" />
            </button>

            {/* User avatar */}
            <button className="flex items-center gap-1.5 p-1.5 rounded-lg hover:bg-neutral-100 transition-colors">
              <div className="w-7 h-7 bg-primary/10 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-neutral-400" />
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="p-6">
        {children}
      </main>
    </div>
  );
}
