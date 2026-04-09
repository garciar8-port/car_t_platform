import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ClipboardList, BarChart3 } from 'lucide-react';

export default function LoginPage() {
  const [step, setStep] = useState<'login' | 'role'>('login');
  const navigate = useNavigate();

  if (step === 'role') {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Activity className="w-8 h-8 text-primary" />
              <span className="text-2xl font-semibold text-primary">BioFlow</span>
            </div>
            <p className="text-neutral-500 text-sm">Select your role</p>
          </div>

          <div className="bg-white border border-neutral-200 rounded-xl p-6">
            <div className="mb-4">
              <p className="text-sm font-medium text-neutral-700">Rockville Site A</p>
              <p className="text-xs text-neutral-400">April 9, 2026</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => navigate('/coordinator')}
                className="flex flex-col items-center gap-3 p-6 border border-neutral-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all group"
              >
                <ClipboardList className="w-10 h-10 text-neutral-400 group-hover:text-primary transition-colors" />
                <span className="font-semibold text-neutral-800">Coordinator</span>
                <span className="text-xs text-neutral-400 text-center">Maya R. · Morning shift</span>
                <span className="text-[10px] text-neutral-400 text-center">Schedule batches, approve recommendations, manage queue</span>
              </button>

              <button
                onClick={() => navigate('/director')}
                className="flex flex-col items-center gap-3 p-6 border border-neutral-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all group"
              >
                <BarChart3 className="w-10 h-10 text-neutral-400 group-hover:text-primary transition-colors" />
                <span className="font-semibold text-neutral-800">Director</span>
                <span className="text-xs text-neutral-400 text-center">David M. · Site Director</span>
                <span className="text-[10px] text-neutral-400 text-center">KPIs, capacity planning, reports, incidents</span>
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
            onClick={() => setStep('role')}
            className="w-full bg-primary text-white font-medium py-3 px-4 rounded-lg hover:bg-primary/90 transition-colors"
          >
            Sign in with SSO
          </button>

          <div className="text-center mt-4">
            <button
              onClick={() => setStep('role')}
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
