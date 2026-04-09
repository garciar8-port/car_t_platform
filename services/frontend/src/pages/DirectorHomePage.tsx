import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import KpiTile from '../components/ui/KpiTile';
import Badge from '../components/ui/Badge';
import { directorKpis as mockKpis, capacityForecastData } from '../data/mock';
import { Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { PlayCircle, FileText, Download, Clock, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';

export default function DirectorHomePage() {
  const navigate = useNavigate();
  const { data: liveKpis } = useApi(() => api.getDirectorKpis(), []);
  const directorKpis = liveKpis || mockKpis;
  const [reportGenerated, setReportGenerated] = useState(false);
  return (
    <AppShell currentUser="David M." siteName="Rockville Site A">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-neutral-900">Good morning, David</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/director/capacity')}
            className="flex items-center gap-1.5 bg-primary text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-primary/90"
          >
            <PlayCircle className="w-4 h-4" /> Run capacity forecast
          </button>
          <button
            onClick={() => { setReportGenerated(true); setTimeout(() => setReportGenerated(false), 3000); }}
            className="flex items-center gap-1.5 border border-neutral-300 text-neutral-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-neutral-50"
          >
            {reportGenerated ? <CheckCircle className="w-4 h-4 text-success" /> : <FileText className="w-4 h-4" />}
            {reportGenerated ? 'Report generated' : 'Generate weekly report'}
          </button>
          <button
            onClick={() => alert('PDF export coming soon')}
            className="flex items-center gap-1.5 border border-neutral-300 text-neutral-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-neutral-50"
          >
            <Download className="w-4 h-4" /> Export to PDF
          </button>
        </div>
      </div>

      {/* Yesterday at a glance */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-3">Yesterday at a glance</h2>
        <div className="grid grid-cols-5 gap-3">
          {directorKpis.map((kpi) => (
            <KpiTile key={kpi.label} {...kpi} large />
          ))}
        </div>
      </section>

      {/* Today's outlook */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-3">Today's outlook</h2>
        <div className="grid grid-cols-2 gap-4">
          {/* Capacity forecast */}
          <div className="bg-white border border-neutral-200 rounded-lg p-5">
            <h3 className="text-sm font-medium text-neutral-700 mb-4">Capacity forecast (next 7 days)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={capacityForecastData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                <YAxis domain={[50, 100]} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                {/* Target band */}
                <Area dataKey={() => 85} fill="#10b981" fillOpacity={0.05} stroke="none" />
                <Area dataKey={() => 75} fill="#ffffff" stroke="none" />
                {/* Lines */}
                <Line type="monotone" dataKey="current" stroke="#1e2761" strokeWidth={2} dot={false} connectNulls={false} />
                <Line type="monotone" dataKey="projected" stroke="#3b82f6" strokeWidth={2} strokeDasharray="6 3" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
            <div className="flex items-center gap-4 mt-2 text-xs text-neutral-400">
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-0.5 bg-primary" />
                <span>Actual</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-0.5 bg-info border-t border-dashed border-info" />
                <span>Projected</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-2 bg-success/10 border border-success/20 rounded-sm" />
                <span>Target range (75-85%)</span>
              </div>
            </div>
          </div>

          {/* Patient pipeline */}
          <div className="bg-white border border-neutral-200 rounded-lg p-5">
            <h3 className="text-sm font-medium text-neutral-700 mb-4">Patient pipeline</h3>
            {/* Stacked bar */}
            <div className="flex h-10 rounded-lg overflow-hidden mb-4">
              <div className="bg-accent flex items-center justify-center text-white text-xs font-medium" style={{ width: `${(3/14)*100}%` }}>3</div>
              <div className="bg-info flex items-center justify-center text-white text-xs font-medium" style={{ width: `${(2/14)*100}%` }}>2</div>
              <div className="bg-neutral-300 flex items-center justify-center text-neutral-600 text-xs font-medium" style={{ width: `${(7/14)*100}%` }}>7</div>
              <div className="bg-warning flex items-center justify-center text-white text-xs font-medium" style={{ width: `${(2/14)*100}%` }}>2</div>
            </div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded bg-accent" />
                <span className="text-neutral-500">In process</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded bg-info" />
                <span className="text-neutral-500">Awaiting cells</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded bg-neutral-300" />
                <span className="text-neutral-500">In queue</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded bg-warning" />
                <span className="text-neutral-500">Urgent</span>
              </div>
            </div>
            <p className="text-xs text-neutral-400 mt-4">14 total patients, 14% urgent share</p>
          </div>
        </div>
      </section>

      {/* Incidents & alerts */}
      <section>
        <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-3">Incidents &amp; alerts</h2>
        <div className="bg-white border border-neutral-200 rounded-lg divide-y divide-neutral-100">
          <div className="flex items-center gap-4 px-4 py-3">
            <Badge variant="warning">Resolved</Badge>
            <div className="flex-1">
              <span className="text-sm text-neutral-700">QC failure on Batch B-1042 — handled by Maya R. — re-scheduling plan applied</span>
            </div>
            <div className="flex items-center gap-1 text-xs text-neutral-400">
              <Clock className="w-3 h-3" />
              Closed at 7:14am
            </div>
            <button onClick={() => navigate('/coordinator/qc-failure/B-1042')} className="text-xs text-primary hover:underline">View details</button>
          </div>
        </div>
      </section>
    </AppShell>
  );
}
