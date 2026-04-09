import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import Badge from '../components/ui/Badge';
import ConfidencePill from '../components/ui/ConfidencePill';
import { escalationPT2493 } from '../data/mock';
import { Shield, CheckCircle, Loader2, X } from 'lucide-react';
import { api } from '../services/api';

export default function UrgentEscalationPage() {
  const { patient, options, timeline } = escalationPT2493;
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showJustification, setShowJustification] = useState(false);
  const [justification, setJustification] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [decided, setDecided] = useState(false);
  const [decidedLabel, setDecidedLabel] = useState('');

  const handleSelectOption = (optId: string) => {
    setSelectedOption(optId);
    setShowJustification(true);
  };

  const handleConfirm = async () => {
    if (!selectedOption || !justification.trim()) return;
    setSubmitting(true);
    const opt = options.find((o) => o.id === selectedOption);
    try {
      await api.selectEscalationOption(patient.id, selectedOption, justification);
    } catch { /* demo fallback */ }
    setDecidedLabel(opt?.label || '');
    setDecided(true);
    setShowJustification(false);
    setSubmitting(false);
  };

  return (
    <AppShell>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-semibold text-neutral-900">Urgent escalation · {patient.id}</h1>
          <Badge variant="danger">{patient.acuityScore} acuity</Badge>
          <span className="text-xs text-neutral-400">(increased from 0.71 yesterday)</span>
        </div>
        <p className="text-sm text-neutral-500">Treating physician request received 12 minutes ago</p>
      </div>

      <div className="grid grid-cols-[1fr_240px] gap-6">
        {/* Options */}
        <div className="grid grid-cols-3 gap-4">
          {options.map((opt) => (
            <div
              key={opt.id}
              className={`bg-white border rounded-lg p-5 flex flex-col ${
                opt.recommended ? 'border-success/40 ring-1 ring-success/20' : 'border-neutral-200'
              }`}
            >
              {/* Badge */}
              <div className="mb-3">
                {opt.badge && (
                  <Badge variant={opt.badgeVariant || 'neutral'}>{opt.badge}</Badge>
                )}
              </div>

              <h3 className="text-sm font-semibold text-neutral-800 mb-4">{opt.label}</h3>

              <div className="space-y-3 flex-1">
                <div>
                  <div className="text-[10px] text-neutral-400 uppercase tracking-wide">Estimated start</div>
                  <div className="text-sm font-medium text-neutral-700">{opt.estimatedStart}</div>
                </div>
                <div>
                  <div className="text-[10px] text-neutral-400 uppercase tracking-wide">Patient impact</div>
                  <div className={`text-sm ${
                    opt.patientImpactLevel === 'high' ? 'text-danger' :
                    opt.patientImpactLevel === 'medium' ? 'text-warning' : 'text-success'
                  }`}>{opt.patientImpact}</div>
                </div>
                <div>
                  <div className="text-[10px] text-neutral-400 uppercase tracking-wide">Operational impact</div>
                  <div className={`text-sm ${
                    opt.operationalImpactLevel === 'high' ? 'text-danger' :
                    opt.operationalImpactLevel === 'medium' ? 'text-warning' : 'text-success'
                  }`}>{opt.operationalImpact}</div>
                </div>
                <div>
                  <ConfidencePill confidence={opt.confidence} />
                </div>
              </div>

              {decided ? (
                selectedOption === opt.id ? (
                  <div className="mt-4 w-full py-2.5 rounded-lg font-medium text-sm text-center text-success flex items-center justify-center gap-2">
                    <CheckCircle className="w-4 h-4" /> Selected
                  </div>
                ) : null
              ) : (
                <button
                  onClick={() => handleSelectOption(opt.id)}
                  className={`mt-4 w-full py-2.5 rounded-lg font-medium text-sm transition-colors ${
                    opt.recommended
                      ? 'bg-primary text-white hover:bg-primary/90'
                      : 'border border-neutral-300 text-neutral-700 hover:bg-neutral-50'
                  }`}
                >
                  Select this option
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Patient timeline */}
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-800 mb-4">Patient timeline</h3>
          <div className="relative">
            <div className="absolute left-2 top-2 bottom-2 w-px bg-neutral-200" />
            <div className="space-y-4">
              {timeline.map((event, i) => (
                <div key={i} className="flex items-start gap-3 relative">
                  <div className={`w-4 h-4 rounded-full border-2 shrink-0 z-10 ${
                    event.highlight ? 'border-danger bg-danger/10' : 'border-neutral-300 bg-white'
                  }`} />
                  <div>
                    <div className={`text-xs font-medium ${event.highlight ? 'text-danger' : 'text-neutral-700'}`}>
                      {event.date}
                    </div>
                    <div className={`text-xs ${event.highlight ? 'text-danger font-medium' : 'text-neutral-500'}`}>
                      {event.event}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="mt-6 bg-neutral-100 border border-neutral-200 rounded-lg px-4 py-3 flex items-center gap-2">
        <Shield className="w-4 h-4 text-neutral-400" />
        <span className="text-xs text-neutral-500">
          {decided
            ? `Decision recorded: ${decidedLabel}. Logged with e-signature.`
            : 'Decision will be logged with e-signature. You will be required to provide justification for your selection.'}
        </span>
      </div>

      {/* Justification modal */}
      {showJustification && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-neutral-900">Confirm selection</h3>
              <button onClick={() => setShowJustification(false)} className="p-1 hover:bg-neutral-100 rounded">
                <X className="w-4 h-4 text-neutral-400" />
              </button>
            </div>
            <p className="text-sm text-neutral-600 mb-4">
              You selected: <strong>{options.find((o) => o.id === selectedOption)?.label}</strong>
            </p>
            <div className="mb-4">
              <label className="text-sm font-medium text-neutral-700 mb-2 block">Justification (required for e-signature)</label>
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                placeholder="Explain your decision..."
                className="w-full h-24 text-sm border border-neutral-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleConfirm}
                disabled={!justification.trim() || submitting}
                className="flex items-center gap-2 bg-primary text-white font-medium py-2.5 px-6 rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                Sign and confirm
              </button>
              <button onClick={() => setShowJustification(false)} className="text-sm text-neutral-500">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
