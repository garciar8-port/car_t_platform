import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import Badge from '../components/ui/Badge';
import { auditEntries as mockAuditEntries } from '../data/mock';
import { Search, Filter, ChevronDown, CheckCircle, Clock, Minus } from 'lucide-react';
import type { AuditEntry } from '../types';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';

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
  const [dateFrom, setDateFrom] = useState('2026-04-01');
  const [dateTo, setDateTo] = useState('2026-04-06');
  const [userFilter, setUserFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');

  const { data: liveAudit } = useApi(() => api.getAuditTrail(), []);
  // Merge live audit entries (from approvals) with mock entries for demo richness
  const auditEntries = [...(liveAudit || []), ...mockAuditEntries];

  const filtered = auditEntries.filter((e) => {
    if (searchPatient && !e.subject.toLowerCase().includes(searchPatient.toLowerCase())) return false;
    if (searchBatch && !e.subject.toLowerCase().includes(searchBatch.toLowerCase())) return false;
    if (userFilter !== 'all' && e.user !== userFilter) return false;
    if (actionFilter !== 'all' && e.actionType !== actionFilter) return false;
    return true;
  });

  const clearFilters = () => {
    setSearchPatient('');
    setSearchBatch('');
    setDateFrom('2026-04-01');
    setDateTo('2026-04-06');
    setUserFilter('all');
    setActionFilter('all');
  };

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
    <AppShell currentUser={(() => { try { const u = sessionStorage.getItem('bioflow_user'); return u ? JSON.parse(u).name : 'QA Reviewer'; } catch { return 'QA Reviewer'; } })()}>
      <h1 className="text-lg font-semibold text-neutral-900 mb-4">Audit trail</h1>

      <div className="grid grid-cols-[1fr_220px] gap-6">
        <div>
          {/* Filters */}
          <div className="bg-white border border-neutral-200 rounded-lg px-4 py-3 flex items-center gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <span className="text-xs text-neutral-400">From:</span>
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="text-xs text-neutral-700 border-none focus:outline-none" />
              <span className="text-xs text-neutral-400">To:</span>
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="text-xs text-neutral-700 border-none focus:outline-none" />
            </div>
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <Filter className="w-3 h-3 text-neutral-400" />
              <select value={userFilter} onChange={(e) => setUserFilter(e.target.value)} className="text-xs text-neutral-700 border-none focus:outline-none bg-transparent">
                <option value="all">All users</option>
                <option value="Maya R.">Maya R.</option>
                <option value="Sarah K.">Sarah K.</option>
                <option value="David M.">David M.</option>
              </select>
            </div>
            <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
              <ChevronDown className="w-3 h-3 text-neutral-400" />
              <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} className="text-xs text-neutral-700 border-none focus:outline-none bg-transparent">
                <option value="all">All actions</option>
                <option value="approve">approve</option>
                <option value="override">override</option>
                <option value="preempt">preempt</option>
                <option value="model_deploy">model_deploy</option>
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
            <button onClick={clearFilters} className="text-xs text-neutral-400 hover:text-primary">Clear</button>
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
              <div className="text-lg font-semibold text-neutral-800">{auditEntries.length}</div>
            </div>
            <div>
              <div className="text-xs text-neutral-400">Override rate</div>
              {(() => {
                const overrides = auditEntries.filter(e => e.actionType === 'override').length;
                const decisions = auditEntries.filter(e => ['approve', 'override'].includes(e.actionType)).length;
                const rate = decisions > 0 ? Math.round((overrides / decisions) * 100) : 0;
                return (<>
                  <div className="text-lg font-semibold text-warning">{rate}%</div>
                  <div className="text-[10px] text-neutral-400">{overrides} of {decisions} recommendations</div>
                </>);
              })()}
            </div>
            <div>
              <div className="text-xs text-neutral-400">Most active user</div>
              <div className="text-sm font-medium text-neutral-700">
                {(() => {
                  const counts: Record<string, number> = {};
                  auditEntries.forEach(e => { counts[e.user] = (counts[e.user] || 0) + 1; });
                  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';
                })()}
              </div>
            </div>
            <div>
              <div className="text-xs text-neutral-400">Most common action</div>
              <div className="text-sm font-medium text-neutral-700">
                {(() => {
                  const counts: Record<string, number> = {};
                  auditEntries.forEach(e => { counts[e.actionType] = (counts[e.actionType] || 0) + 1; });
                  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';
                })()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
