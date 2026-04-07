import { useState } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import ConfidencePill from '../components/ui/ConfidencePill';
import { patientPT2487, recommendationPT2487 } from '../data/mock';
import { ChevronRight, ChevronDown, ExternalLink, Flag } from 'lucide-react';

export default function PatientAssignmentPage() {
  const [showShap, setShowShap] = useState(false);
  const rec = recommendationPT2487;
  const patient = patientPT2487;

  return (
    <AppShell>
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-neutral-400 mb-4">
        <Link to="/coordinator" className="hover:text-primary">Home</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span>Patient queue</span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-neutral-700 font-medium">{patient.id} assignment</span>
      </nav>

      <div className="grid grid-cols-[60%_40%] gap-6">
        {/* Left: Recommendation */}
        <div className="space-y-4">
          <div className="bg-white border border-neutral-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-lg font-semibold text-neutral-900">
                  Recommended: Assign to {rec.recommendedSuiteName}, start {rec.recommendedStartTime.toLowerCase()}
                </h1>
              </div>
              <ConfidencePill confidence={rec.confidence} size="lg" />
            </div>

            {/* Alternatives */}
            <div className="space-y-2 mb-4">
              <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Alternatives</h3>
              {rec.alternatives.map((alt, i) => (
                <div key={alt.suiteId} className="border border-neutral-100 rounded-lg p-3 flex items-center justify-between hover:bg-neutral-50">
                  <div>
                    <span className="text-sm font-medium text-neutral-700">Alternative {i + 1}: {alt.suiteName}</span>
                    <span className="text-sm text-neutral-500 ml-1">· start {alt.startTime.toLowerCase()}</span>
                    <span className="text-xs text-neutral-400 ml-2">— {alt.tradeoff}</span>
                  </div>
                  <ConfidencePill confidence={alt.confidence} />
                </div>
              ))}
            </div>

            {/* SHAP Explanation */}
            <button
              onClick={() => setShowShap(!showShap)}
              className="flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 mb-3"
            >
              {showShap ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Why this recommendation?
            </button>
            {showShap && (
              <div className="bg-neutral-50 border border-neutral-100 rounded-lg p-4 mb-4 space-y-2">
                {rec.shapFactors.map((f, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className={`mt-1 w-1.5 h-1.5 rounded-full shrink-0 ${f.direction === 'positive' ? 'bg-success' : 'bg-danger'}`} />
                    <span className="text-sm text-neutral-600">{f.factor}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 pt-2 border-t border-neutral-100">
              <button className="bg-primary text-white font-medium py-2.5 px-6 rounded-lg hover:bg-primary/90 transition-colors">
                Approve recommendation
              </button>
              <button className="border border-neutral-300 text-neutral-700 font-medium py-2.5 px-6 rounded-lg hover:bg-neutral-50 transition-colors">
                Override and choose differently
              </button>
            </div>
            <button className="flex items-center gap-1 text-xs text-neutral-400 hover:text-primary mt-3">
              <Flag className="w-3 h-3" />
              Flag for supervisor review
            </button>
          </div>
        </div>

        {/* Right: Patient Context */}
        <div className="bg-white border border-neutral-200 rounded-lg p-6">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-3">Patient context</h2>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg font-semibold text-neutral-900">{patient.id}</span>
              <span className="text-neutral-300">·</span>
              <span className="text-sm text-neutral-600">{patient.indication}</span>
              <span className="text-neutral-300">·</span>
              <span className="text-sm text-neutral-600">{patient.sex}, {patient.age}</span>
            </div>
          </div>

          {/* Acuity */}
          <div className="border border-neutral-100 rounded-lg p-3 mb-4">
            <div className="text-xs text-neutral-400 mb-1">Acuity score</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-semibold text-warning">{patient.acuityScore}</span>
              <span className="text-xs text-neutral-400">(medium-high)</span>
            </div>
          </div>

          {/* Key dates */}
          <div className="space-y-2 mb-4">
            <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Key dates</div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-neutral-400">Apheresis scheduled</div>
              <div className="text-neutral-700">{patient.apheresisDate}</div>
              <div className="text-neutral-400">Cells expected</div>
              <div className="text-neutral-700">{patient.cellsExpectedDate}</div>
              <div className="text-neutral-400">Target infusion</div>
              <div className="text-neutral-700">{patient.targetInfusionWindow.start} – {patient.targetInfusionWindow.end}</div>
            </div>
          </div>

          {/* Treatment center */}
          <div className="space-y-2 mb-4">
            <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Treatment center</div>
            <div className="text-sm text-neutral-700">{patient.treatmentCenter}</div>
          </div>

          {/* Bridging therapy */}
          <div className="space-y-2 mb-4">
            <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Bridging therapy</div>
            <div className="text-sm text-neutral-700">{patient.bridgingTherapy}</div>
          </div>

          {/* Clinical notes */}
          <div className="space-y-2 mb-4">
            <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Clinical notes</div>
            <div className="text-sm text-neutral-600 leading-relaxed">{patient.clinicalNotes}</div>
          </div>

          <button className="flex items-center gap-1.5 text-sm text-primary hover:text-primary/80 font-medium">
            Open in Vineti
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </AppShell>
  );
}
