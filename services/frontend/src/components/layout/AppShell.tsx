import { useState, useRef, useEffect } from 'react';
import { Bell, ChevronDown, Activity, User, LogOut, Settings, FileText } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setShowNotifications(false);
      if (userRef.current && !userRef.current.contains(e.target as Node)) setShowUserMenu(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Top Bar */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 h-14">
          {/* Left: Logo */}
          <Link to="/coordinator" className="flex items-center gap-2">
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
            <div className="relative" ref={notifRef}>
              <button
                onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false); }}
                className="relative p-2 rounded-lg hover:bg-neutral-100 transition-colors"
              >
                <Bell className="w-5 h-5 text-neutral-500" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full" />
              </button>
              {showNotifications && (
                <div className="absolute right-0 top-full mt-1 w-72 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
                  <div className="px-3 py-2 border-b border-neutral-100 text-xs font-medium text-neutral-500">Notifications</div>
                  <div className="divide-y divide-neutral-50">
                    <button onClick={() => { navigate('/coordinator/escalation/PT-2493'); setShowNotifications(false); }} className="w-full text-left px-3 py-2.5 hover:bg-neutral-50">
                      <div className="text-xs font-medium text-danger">Urgent: PT-2493 escalation</div>
                      <div className="text-[10px] text-neutral-400 mt-0.5">12 minutes ago</div>
                    </button>
                    <button onClick={() => { navigate('/coordinator/qc-failure/B-1042'); setShowNotifications(false); }} className="w-full text-left px-3 py-2.5 hover:bg-neutral-50">
                      <div className="text-xs font-medium text-neutral-700">QC failure: Batch B-1042</div>
                      <div className="text-[10px] text-neutral-400 mt-0.5">2 hours ago</div>
                    </button>
                    <div className="px-3 py-2.5">
                      <div className="text-xs text-neutral-600">Suite 4 cleaning complete</div>
                      <div className="text-[10px] text-neutral-400 mt-0.5">45 minutes ago</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* User avatar */}
            <div className="relative" ref={userRef}>
              <button
                onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false); }}
                className="flex items-center gap-1.5 p-1.5 rounded-lg hover:bg-neutral-100 transition-colors"
              >
                <div className="w-7 h-7 bg-primary/10 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-neutral-400" />
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
                  <div className="px-3 py-2 border-b border-neutral-100">
                    <div className="text-sm font-medium text-neutral-800">{currentUser}</div>
                    <div className="text-[10px] text-neutral-400">{siteName} · {shiftLabels[currentShift]}</div>
                  </div>
                  <button onClick={() => { navigate('/coordinator/handoff'); setShowUserMenu(false); }} className="w-full text-left px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-50 flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5" /> Shift handoff
                  </button>
                  <button onClick={() => { navigate('/audit'); setShowUserMenu(false); }} className="w-full text-left px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-50 flex items-center gap-2">
                    <Settings className="w-3.5 h-3.5" /> Audit trail
                  </button>
                  <button onClick={() => { navigate('/'); setShowUserMenu(false); }} className="w-full text-left px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-50 flex items-center gap-2 border-t border-neutral-100">
                    <LogOut className="w-3.5 h-3.5" /> Sign out
                  </button>
                </div>
              )}
            </div>
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
