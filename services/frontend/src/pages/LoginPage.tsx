import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Sun, Sunset, Moon } from 'lucide-react';
import type { Shift } from '../types';

export default function LoginPage() {
  const [step, setStep] = useState<'login' | 'shift'>('login');
  const navigate = useNavigate();

  const handleShiftSelect = (shift: Shift) => {
    void shift;
    navigate('/coordinator');
  };

  if (step === 'shift') {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="w-full max-w-lg">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Activity className="w-8 h-8 text-primary" />
              <span className="text-2xl font-semibold text-primary">BioFlow</span>
            </div>
            <p className="text-neutral-500 text-sm">Select your shift</p>
          </div>

          <div className="bg-white border border-neutral-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-sm font-medium text-neutral-700">Rockville Site A</p>
                <p className="text-xs text-neutral-400">April 6, 2026</p>
              </div>
              <button className="text-xs text-primary hover:underline">Change site</button>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {([
                { shift: 'morning' as Shift, label: 'Morning', time: '7am – 3pm', icon: Sun },
                { shift: 'afternoon' as Shift, label: 'Afternoon', time: '3pm – 11pm', icon: Sunset },
                { shift: 'night' as Shift, label: 'Night', time: '11pm – 7am', icon: Moon },
              ]).map(({ shift, label, time, icon: Icon }) => (
                <button
                  key={shift}
                  onClick={() => handleShiftSelect(shift)}
                  className="flex flex-col items-center gap-2 p-6 border border-neutral-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all group"
                >
                  <Icon className="w-8 h-8 text-neutral-400 group-hover:text-primary transition-colors" />
                  <span className="font-medium text-neutral-800">{label}</span>
                  <span className="text-xs text-neutral-400">{time}</span>
                </button>
              ))}
            </div>
          </div>

          <p className="text-center text-xs text-neutral-400 mt-6">
            21 CFR Part 11 compliant · v2.1.4 · Audit logging enabled
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Activity className="w-10 h-10 text-primary" />
            <span className="text-3xl font-semibold text-primary">BioFlow</span>
          </div>
          <p className="text-neutral-500">Manufacturing Scheduler</p>
        </div>

        <div className="bg-white border border-neutral-200 rounded-xl p-8">
          <button
            onClick={() => setStep('shift')}
            className="w-full bg-primary text-white font-medium py-3 px-4 rounded-lg hover:bg-primary/90 transition-colors"
          >
            Sign in with SSO
          </button>

          <div className="text-center mt-4">
            <button
              onClick={() => setStep('shift')}
              className="text-sm text-neutral-500 hover:text-primary transition-colors"
            >
              Sign in with email
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-neutral-400 mt-6">
          21 CFR Part 11 compliant · v2.1.4 · Audit logging enabled
        </p>
      </div>
    </div>
  );
}
