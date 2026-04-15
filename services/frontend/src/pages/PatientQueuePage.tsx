import { useState } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import Badge from '../components/ui/Badge';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Search, Filter, ChevronRight, AlertTriangle, Loader2 } from 'lucide-react';
import { patients as mockPatients } from '../data/mock';

type StatusFilter = 'all' | 'awaiting_assignment' | 'in_progress' | 'urgent';

const statusBadge: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
  awaiting_assignment: 'info',
  in_progress: 'success',
  completed: 'neutral',
  urgent: 'danger',
};

export default function PatientQueuePage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [sortBy, setSortBy] = useState<'acuity' | 'date' | 'name'>('acuity');

  const { data: livePatients, loading } = useApi(() => api.getPatientQueue(), []);
  const patients = livePatients || mockPatients || [];

  const filtered = patients
    .filter((p) => {
      if (search && !p.id.toLowerCase().includes(search.toLowerCase()) && !p.indication.toLowerCase().includes(search.toLowerCase())) return false;
      if (statusFilter === 'urgent' && !p.isUrgent) return false;
      if (statusFilter !== 'all' && statusFilter !== 'urgent' && p.status !== statusFilter) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'acuity') return b.acuityScore - a.acuityScore;
      if (sortBy === 'date') return a.enrollmentDate.localeCompare(b.enrollmentDate);
      return a.id.localeCompare(b.id);
    });

  const urgentCount = patients.filter((p) => p.isUrgent).length;
  const awaitingCount = patients.filter((p) => p.status === 'awaiting_assignment').length;

  return (
    <AppShell>
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-neutral-400 mb-4">
        <Link to="/coordinator" className="hover:text-primary">Home</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-neutral-700 font-medium">Patient queue</span>
      </nav>

      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-neutral-900">Patient queue</h1>
        <div className="flex items-center gap-2 text-xs text-neutral-400">
          {loading && <Loader2 className="w-3 h-3 animate-spin" />}
          {patients.length} patients · {awaitingCount} awaiting assignment
          {urgentCount > 0 && (
            <span className="flex items-center gap-1 text-danger font-medium">
              · <AlertTriangle className="w-3 h-3" /> {urgentCount} urgent
            </span>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border border-neutral-200 rounded-lg px-4 py-3 flex items-center gap-3 mb-4">
        <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5 flex-1 max-w-xs">
          <Search className="w-3 h-3 text-neutral-400" />
          <input
            type="text"
            placeholder="Search by patient ID or indication..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="text-xs text-neutral-700 border-none focus:outline-none w-full"
          />
        </div>
        <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
          <Filter className="w-3 h-3 text-neutral-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="text-xs text-neutral-700 border-none focus:outline-none bg-transparent"
          >
            <option value="all">All statuses</option>
            <option value="awaiting_assignment">Awaiting assignment</option>
            <option value="in_progress">In progress</option>
            <option value="urgent">Urgent only</option>
          </select>
        </div>
        <div className="flex items-center gap-1.5 border border-neutral-200 rounded-lg px-3 py-1.5">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'acuity' | 'date' | 'name')}
            className="text-xs text-neutral-700 border-none focus:outline-none bg-transparent"
          >
            <option value="acuity">Sort by acuity (highest first)</option>
            <option value="date">Sort by enrollment date</option>
            <option value="name">Sort by patient ID</option>
          </select>
        </div>
      </div>

      {/* Patient table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[100px_120px_80px_100px_140px_120px_100px_40px] gap-3 px-4 py-2 bg-neutral-50 border-b border-neutral-100 text-[10px] font-medium text-neutral-400 uppercase tracking-wide">
          <span>Patient ID</span>
          <span>Indication</span>
          <span>Acuity</span>
          <span>Status</span>
          <span>Infusion window</span>
          <span>Treatment center</span>
          <span>Enrolled</span>
          <span></span>
        </div>

        {/* Rows */}
        <div className="divide-y divide-neutral-50">
          {filtered.map((patient) => (
            <Link
              key={patient.id}
              to={`/coordinator/assignment/${patient.id}`}
              className="grid grid-cols-[100px_120px_80px_100px_140px_120px_100px_40px] gap-3 px-4 py-3 text-sm items-center hover:bg-neutral-50 cursor-pointer"
            >
              <span className="text-primary font-medium text-xs flex items-center gap-1.5">
                {patient.isUrgent && <AlertTriangle className="w-3 h-3 text-danger" />}
                {patient.id}
              </span>
              <span className="text-neutral-700 text-xs">{patient.indication}</span>
              <span className={`text-xs font-semibold ${
                patient.acuityScore >= 0.8 ? 'text-danger' :
                patient.acuityScore >= 0.5 ? 'text-warning' : 'text-neutral-600'
              }`}>
                {patient.acuityScore.toFixed(2)}
              </span>
              <Badge variant={statusBadge[patient.status] || 'neutral'}>
                {patient.status.replace('_', ' ')}
              </Badge>
              <span className="text-neutral-600 text-xs">
                {patient.targetInfusionWindow.start} – {patient.targetInfusionWindow.end}
              </span>
              <span className="text-neutral-500 text-xs truncate">{patient.treatmentCenter}</span>
              <span className="text-neutral-400 text-xs">{patient.enrollmentDate}</span>
              <ChevronRight className="w-4 h-4 text-neutral-300" />
            </Link>
          ))}
          {filtered.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-neutral-400">
              No patients match your filters
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
