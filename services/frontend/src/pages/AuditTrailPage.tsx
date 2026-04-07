import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import Badge from '../components/ui/Badge';
import { auditEntries } from '../data/mock';
import { Search, Filter, ChevronDown, CheckCircle, Clock, Minus } from 'lucide-react';
import type { AuditEntry } from '../types';

const actionColors: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
  approve: 'success',
  override: 'warning',
  preempt: 'danger',
  model_deploy: 'info',
};

const signatureIcons: Record<string, typeof CheckCircle> = {
  signed: CheckCircle,
  pending: Clock,
  na: Minus,
};

export default function AuditTrailPage() {
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [searchPatient, setSearchPatient] = useState('');
  const [searchBatch, setSearchBatch] = useState('');

  const filtered = auditEntries.filter((e) => {
    if (searchPatient && !e.subject.toLowerCase().includes(searchPatient.toLowerCase())) return false;
    if (searchBatch && !e.subject.toLowerCase().includes(searchBatch.toLowerCase())) return false;
    return true;
  });

  const renderRow = (entry: AuditEntry) => {
    const isExpanded = expandedRow === entry.id;
    const SigIcon = signatureIcons[entry.signatureStatus] || Minus;

    return (
      <div key={entry.id}>
        <div
          onClick={() => setExpandedRow(isExpanded ? null : entry.id)}
          className={`grid grid-cols-[140px_90px_80px_90px_1fr_100px_50px] gap-3 px-4 py-3 text-sm cursor-pointer hover:bg-neutral-50 items-center ${
            isExpanded ? 'bg-neutral-50' : ''
          }`}
        >
          <span className="text-neutral-500 text-xs">{entry.timestamp}</span>
          <span className="text-neutral-700 font-medium text-xs">{entry.user}</span>
          <Badge variant={actionColors[entry.actionType] || 'neutral'}>{entry.actionType}</Badge>
          <span className="text-primary text-xs font-medium">{entry.subject}</span>
          <span className="text-neutral-600 text-xs truncate">{entry.details}</span>
          <span className="text-neutral-400 text-[10px]">{entry.modelVersion}</span>
          <SigIcon className={`w-4 h-4 ${
            entry.signatureStatus === 'signed' ? 'text-success' :
            entry.signatureStatus === 'pending' ? 'text-warning' : 'text-neutral-300'
          }`} />
        </div>
        {isExpanded && (
          <div className="bg-neutral-50 border-t border-neutral-100 px-4 py-3 grid grid-cols-2 gap-4">
            <div>
              <div className="text-[10px] text-neutral-400 uppercase tracking-wide mb-1">Full details</div>
              <div className="text-sm text-neutral-600">{entry.details}</div>
              {entry.justification && (
                <>
                  <div className="text-[10px] text-neutral-400 uppercase tracking-wide mt-3 mb-1">Justification</div>
                  <div className="text-sm text-neutral-600">{entry.justification}</div>
                </>
              )}
            </div>
            <div>
              <div className="text-[10px] text-neutral-400 uppercase tracking-wide mb-1">Signature</div>
              <div className="text-sm text-neutral-600 capitalize">{entry.signatureStatus}</div>
              <div className="text-[10px] text-neutral-400 uppercase tracking-wide mt-3 mb-1">Model version</div>
              <div className="text-sm text-neutral-600">{entry.modelVersion}</div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <AppShell currentUser="QA Reviewer">
      <h1 className="text-lg font-semibold text-neutral-900 mb-4">Audit trail</h1>

      <div className="grid grid-cols-[1fr_220px] gap-6">
        <div>
          {/* Filters */}
          <div className="bg-white border border-neutral-200 rounded-lg px-4 py-3 flex items-center gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <span className="text-xs text-neutral-400">From:</span>
              <input type="date" defaultValue="2026-04-01" className="text-xs text-neutral-700 border-none focus:outline-none" />
              <span className="text-xs text-neutral-400">To:</span>
              <input type="date" defaultValue="2026-04-06" className="text-xs text-neutral-700 border-none focus:outline-none" />
            </div>
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <Filter className="w-3 h-3 text-neutral-400" />
              <select className="text-xs text-neutral-700 border-none focus:outline-none bg-transparent">
                <option>All users</option>
                <option>Maya R.</option>
                <option>Sarah K.</option>
                <option>David M.</option>
              </select>
            </div>
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <ChevronDown className="w-3 h-3 text-neutral-400" />
              <select className="text-xs text-neutral-700 border-none focus:outline-none bg-transparent">
                <option>All actions</option>
                <option>approve</option>
                <option>override</option>
                <option>preempt</option>
                <option>model_deploy</option>
              </select>
            </div>
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <Search className="w-3 h-3 text-neutral-400" />
              <input
                type="text"
                placeholder="Patient ID"
                value={searchPatient}
                onChange={(e) => setSearchPatient(e.target.value)}
                className="text-xs text-neutral-700 border-none focus:outline-none w-20"
              />
            </div>
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <Search className="w-3 h-3 text-neutral-400" />
              <input
                type="text"
                placeholder="Batch ID"
                value={searchBatch}
                onChange={(e) => setSearchBatch(e.target.value)}
                className="text-xs text-neutral-700 border-none focus:outline-none w-20"
              />
            </div>
            <button className="text-xs text-neutral-400 hover:text-primary">Clear</button>
          </div>

          {/* Table */}
          <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="grid grid-cols-[140px_90px_80px_90px_1fr_100px_50px] gap-3 px-4 py-2 bg-neutral-50 border-b border-neutral-100 text-[10px] font-medium text-neutral-400 uppercase tracking-wide">
              <span>Timestamp</span>
              <span>User</span>
              <span>Action</span>
              <span>Subject</span>
              <span>Details</span>
              <span>Model</span>
              <span>Sig</span>
            </div>
            {/* Rows */}
            <div className="divide-y divide-neutral-50">
              {filtered.map(renderRow)}
            </div>
          </div>
        </div>

        {/* Right: Quick stats */}
        <div className="bg-white border border-neutral-200 rounded-lg p-4 h-fit">
          <h3 className="text-sm font-semibold text-neutral-800 mb-4">Quick stats</h3>
          <div className="space-y-3">
            <div>
              <div className="text-xs text-neutral-400">Total entries</div>
              <div className="text-lg font-semibold text-neutral-800">247</div>
            </div>
            <div>
              <div className="text-xs text-neutral-400">Override rate</div>
              <div className="text-lg font-semibold text-warning">14%</div>
              <div className="text-[10px] text-neutral-400">32 of 234 recommendations</div>
            </div>
            <div>
              <div className="text-xs text-neutral-400">Most active user</div>
              <div className="text-sm font-medium text-neutral-700">Maya R.</div>
            </div>
            <div>
              <div className="text-xs text-neutral-400">Most overridden type</div>
              <div className="text-sm font-medium text-neutral-700">preempt</div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
