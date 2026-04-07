import AppShell from '../components/layout/AppShell';
import Badge from '../components/ui/Badge';
import ConfidencePill from '../components/ui/ConfidencePill';
import { escalationPT2493 } from '../data/mock';
import { Shield } from 'lucide-react';

export default function UrgentEscalationPage() {
  const { patient, options, timeline } = escalationPT2493;

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

              <button
                className={`mt-4 w-full py-2.5 rounded-lg font-medium text-sm transition-colors ${
                  opt.recommended
                    ? 'bg-primary text-white hover:bg-primary/90'
                    : 'border border-neutral-300 text-neutral-700 hover:bg-neutral-50'
                }`}
              >
                Select this option
              </button>
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
          Decision will be logged with e-signature. You will be required to provide justification for your selection.
        </span>
      </div>
    </AppShell>
  );
}
