import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import { AlertCircle, ChevronDown, ChevronRight, ExternalLink, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export default function QcFailurePage() {
  const [showChanges, setShowChanges] = useState(false);
  const [planState, setPlanState] = useState<'pending' | 'applying' | 'applied' | 'rejected'>('pending');
  const [notifState, setNotifState] = useState<'idle' | 'sending' | 'sent'>('idle');
  const [notifications, setNotifications] = useState({
    physician: true,
    clinicalSite: true,
    qaTeam: true,
    vpOps: false,
  });

  const handleApplyPlan = async () => {
    setPlanState('applying');
    try {
      await api.applyReschedule('B-1042');
    } catch { /* demo fallback */ }
    setPlanState('applied');
  };

  const handleReject = async () => {
    try {
      await api.rejectReschedule('B-1042');
    } catch { /* demo fallback */ }
    setPlanState('rejected');
  };

  const handleSendNotifications = async () => {
    setNotifState('sending');
    try {
      await api.sendNotifications('B-1042', notifications);
    } catch { /* demo fallback */ }
    setNotifState('sent');
  };

  return (
    <AppShell>
      {/* Red alert banner */}
      <div className="bg-danger/5 border border-danger/20 rounded-lg px-4 py-3 flex items-center gap-3 mb-6">
        <AlertCircle className="w-5 h-5 text-danger shrink-0" />
        <div className="flex-1">
          <span className="text-sm font-semibold text-danger">QC Failure</span>
          <span className="text-sm text-neutral-700 ml-2">
            Batch B-1042 · Patient PT-2401 · Failed sterility test at 11:42pm
          </span>
        </div>
        <button className="flex items-center gap-1 text-xs text-primary hover:underline">
          View QC report <ExternalLink className="w-3 h-3" />
        </button>
      </div>

      <div className="grid grid-cols-[1fr_280px] gap-6">
        <div className="space-y-6">
          {/* Cascade impact */}
          <div className="bg-white border border-neutral-200 rounded-lg p-6">
            <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-4">
              Schedule cascade impact (without re-optimization)
            </h2>
            <div className="relative">
              {/* Timeline visualization */}
              <div className="flex items-center mb-2">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                  <div key={day} className="flex-1 text-center text-[10px] text-neutral-400">{day}</div>
                ))}
              </div>
              <div className="relative h-32 bg-neutral-50 rounded border border-neutral-100">
                {/* Disruption line */}
                <div className="absolute top-0 bottom-0 left-[14%] w-0.5 bg-danger z-10">
                  <div className="absolute -top-1 -left-1 w-2.5 h-2.5 bg-danger rounded-full" />
                  <div className="absolute -top-5 -left-6 text-[10px] text-danger font-medium whitespace-nowrap">QC Failure</div>
                </div>
                {/* Original schedule bars (faded) */}
                <div className="absolute top-3 left-[2%] w-[40%] h-5 bg-neutral-200 rounded opacity-50" />
                <div className="absolute top-3 left-[45%] w-[25%] h-5 bg-neutral-200 rounded opacity-50" />
                <div className="absolute top-10 left-[15%] w-[30%] h-5 bg-neutral-200 rounded opacity-50 border-2 border-danger/40" />
                <div className="absolute top-10 left-[48%] w-[20%] h-5 bg-neutral-200 rounded opacity-50 border-2 border-danger/40" />
                <div className="absolute top-[68px] left-[5%] w-[35%] h-5 bg-neutral-200 rounded opacity-50" />
                <div className="absolute top-[68px] left-[42%] w-[28%] h-5 bg-neutral-200 rounded opacity-50 border-2 border-danger/40" />
                <div className="absolute top-[92px] left-[20%] w-[25%] h-5 bg-neutral-200 rounded opacity-50 border-2 border-danger/40" />
              </div>
              <div className="flex items-center gap-4 mt-3 text-xs text-neutral-500">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-2 bg-neutral-200 rounded opacity-50" />
                  <span>Original schedule</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-2 bg-neutral-200 rounded border-2 border-danger/40" />
                  <span>Affected batches</span>
                </div>
              </div>
              <p className="text-sm text-danger font-medium mt-2">
                4 patients affected, average wait increase 2.3 days
              </p>
            </div>
          </div>

          {/* Recommended re-scheduling plan */}
          <div className="bg-white border border-success/30 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-5 h-5 bg-success/10 rounded-full flex items-center justify-center">
                <span className="text-success text-xs">&#10003;</span>
              </span>
              <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                Recommended re-scheduling plan
              </h2>
            </div>

            {/* New timeline */}
            <div className="relative h-24 bg-success/5 rounded border border-success/10 mb-4">
              <div className="absolute top-3 left-[2%] w-[40%] h-5 bg-accent/20 rounded border border-accent/30" />
              <div className="absolute top-3 left-[45%] w-[25%] h-5 bg-info/20 rounded border border-info/30" />
              <div className="absolute top-10 left-[20%] w-[30%] h-5 bg-accent/20 rounded border border-accent/30" />
              <div className="absolute top-10 left-[52%] w-[20%] h-5 bg-info/20 rounded border border-info/30" />
              <div className="absolute top-[68px] left-[5%] w-[35%] h-5 bg-accent/20 rounded border border-accent/30" />
              <div className="absolute top-[68px] left-[45%] w-[28%] h-5 bg-info/20 rounded border border-info/30" />
            </div>

            <p className="text-sm text-success font-medium mb-3">
              Re-scheduled to minimize patient impact: 2 patients affected, average wait increase 0.6 days
            </p>

            {/* What changed */}
            <button
              onClick={() => setShowChanges(!showChanges)}
              className="flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 mb-3"
            >
              {showChanges ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              What changed?
            </button>
            {showChanges && (
              <div className="bg-neutral-50 rounded-lg p-3 space-y-2 mb-4">
                <div className="flex items-start gap-2 text-sm text-neutral-600">
                  <span className="text-neutral-400 shrink-0">1.</span>
                  Batch B-1043 moved from Suite 2 to Suite 5
                </div>
                <div className="flex items-start gap-2 text-sm text-neutral-600">
                  <span className="text-neutral-400 shrink-0">2.</span>
                  Batch B-1045 delayed by 8 hours
                </div>
                <div className="flex items-start gap-2 text-sm text-neutral-600">
                  <span className="text-neutral-400 shrink-0">3.</span>
                  Patient PT-2401 will need re-collection — clinical site notified
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 pt-3 border-t border-neutral-100">
              {planState === 'applied' ? (
                <div className="flex items-center gap-2 text-success font-medium py-2.5 px-6">
                  <CheckCircle className="w-5 h-5" />
                  Re-scheduling plan applied
                </div>
              ) : planState === 'rejected' ? (
                <div className="flex items-center gap-2 text-warning font-medium py-2.5 px-6">
                  Plan rejected — manual handling required
                </div>
              ) : (
                <>
                  <button
                    onClick={handleApplyPlan}
                    disabled={planState === 'applying'}
                    className="flex items-center gap-2 bg-primary text-white font-medium py-2.5 px-6 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
                  >
                    {planState === 'applying' && <Loader2 className="w-4 h-4 animate-spin" />}
                    Apply re-scheduling plan
                  </button>
                  <button className="border border-neutral-300 text-neutral-700 font-medium py-2.5 px-6 rounded-lg hover:bg-neutral-50 transition-colors">
                    Modify plan
                  </button>
                  <button onClick={handleReject} className="text-sm text-neutral-400 hover:text-primary">
                    Reject and handle manually
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right: Notify stakeholders */}
        <div className="bg-white border border-neutral-200 rounded-lg p-4 h-fit">
          <h3 className="text-sm font-semibold text-neutral-800 mb-4">Notify stakeholders</h3>
          <div className="space-y-3">
            {[
              { key: 'physician', label: 'Treating physician for PT-2401' },
              { key: 'clinicalSite', label: 'Clinical site coordinator' },
              { key: 'qaTeam', label: 'QA team' },
              { key: 'vpOps', label: 'VP of Operations (only if requested)' },
            ].map(({ key, label }) => (
              <label key={key} className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications[key as keyof typeof notifications]}
                  onChange={(e) => setNotifications((prev) => ({ ...prev, [key]: e.target.checked }))}
                  className="mt-0.5 rounded border-neutral-300 text-primary focus:ring-primary/20"
                />
                <span className="text-sm text-neutral-600">{label}</span>
              </label>
            ))}
          </div>
          <button
            onClick={handleSendNotifications}
            disabled={notifState !== 'idle'}
            className="w-full mt-4 bg-primary text-white text-sm font-medium py-2 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {notifState === 'sending' ? 'Sending...' : notifState === 'sent' ? 'Notifications sent' : 'Send notifications'}
          </button>
        </div>
      </div>
    </AppShell>
  );
}
