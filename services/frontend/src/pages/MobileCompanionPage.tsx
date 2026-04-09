import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Badge from '../components/ui/Badge';
import ConfidencePill from '../components/ui/ConfidencePill';
import { Activity, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export default function MobileCompanionPage() {
  const navigate = useNavigate();
  const [actionState, setActionState] = useState<'idle' | 'approving' | 'approved' | 'declined'>('idle');

  const handleApprove = async () => {
    setActionState('approving');
    try {
      await api.selectEscalationOption('PT-2493', 'expedite', 'Approved via mobile', 'Maya R.');
    } catch { /* demo fallback */ }
    setActionState('approved');
  };

  const handleDecline = () => {
    setActionState('declined');
  };
  return (
    <div className="min-h-screen bg-neutral-100 flex items-center justify-center p-4">
      <div className="w-[375px] bg-white rounded-2xl shadow-lg overflow-hidden border border-neutral-200">
        {/* App header */}
        <div className="bg-primary px-4 py-3 flex items-center gap-2">
          <Activity className="w-5 h-5 text-white" />
          <span className="text-white font-semibold">BioFlow</span>
        </div>

        {/* Notification banner */}
        <div className="bg-danger/5 border-b border-danger/10 px-4 py-2.5 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-danger" />
          <span className="text-sm font-medium text-danger">1 urgent action required</span>
        </div>

        {/* Action card */}
        <div className="p-4">
          <div className="border border-neutral-200 rounded-xl p-4 mb-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg font-semibold text-neutral-900">PT-2493</span>
              <Badge variant="danger">0.94 acuity</Badge>
            </div>

            <p className="text-sm text-neutral-600 mb-3">
              PT-2493 deteriorating — physician requests expedited slot
            </p>

            <div className="bg-neutral-50 rounded-lg p-3 mb-4">
              <div className="text-xs text-neutral-400 mb-1">Recommendation</div>
              <div className="text-sm font-medium text-neutral-800">Expedite to April 8 (2 days from now)</div>
              <div className="mt-2">
                <ConfidencePill confidence={91} />
              </div>
            </div>

            <div className="space-y-2">
              {actionState === 'approved' ? (
                <div className="w-full flex items-center justify-center gap-2 text-success font-medium py-3">
                  <CheckCircle className="w-5 h-5" /> Approved
                </div>
              ) : actionState === 'declined' ? (
                <div className="w-full text-center text-warning font-medium py-3">
                  Declined — team notified
                </div>
              ) : (
                <>
                  <button
                    onClick={handleApprove}
                    disabled={actionState === 'approving'}
                    className="w-full flex items-center justify-center gap-2 bg-primary text-white font-medium py-3 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
                  >
                    {actionState === 'approving' && <Loader2 className="w-4 h-4 animate-spin" />}
                    Approve recommendation
                  </button>
                  <button
                    onClick={() => navigate('/coordinator/escalation/PT-2493')}
                    className="w-full border border-neutral-300 text-neutral-700 font-medium py-3 rounded-lg hover:bg-neutral-50 transition-colors"
                  >
                    Open full details
                  </button>
                </>
              )}
            </div>

            {actionState === 'idle' && (
              <div className="text-center mt-3">
                <button onClick={handleDecline} className="text-sm text-neutral-400 hover:text-primary">Decline and call team</button>
              </div>
            )}
          </div>

          {/* Other notifications */}
          <div className="border-t border-neutral-100 pt-3">
            <div className="text-xs text-neutral-400 mb-2">Other notifications</div>
            <div className="text-xs text-neutral-500">Suite 4 cleaning complete · 45m ago</div>
            <div className="text-xs text-neutral-500 mt-1">Shift handoff from Sarah · 1h ago</div>
          </div>
        </div>

        {/* Bottom status */}
        <div className="bg-neutral-50 border-t border-neutral-100 px-4 py-3 text-center">
          <span className="text-xs text-neutral-400">On call · Maya R. · 9:42pm</span>
        </div>
      </div>
    </div>
  );
}
