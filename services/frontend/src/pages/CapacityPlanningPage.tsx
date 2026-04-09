import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import { throughputSimData } from '../data/mock';
import { ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { PlayCircle, Save, GitCompare, Download, Loader2, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const bottleneckData = [
  { name: 'Suite capacity', value: 40 },
  { name: 'QC throughput', value: 30 },
  { name: 'Cell expansion variability', value: 20 },
  { name: 'Patient arrival timing', value: 10 },
];

export default function CapacityPlanningPage() {
  const [suiteCount, setSuiteCount] = useState(6);
  const [arrivalRate, setArrivalRate] = useState(1.8);
  const [qcFailRate, setQcFailRate] = useState(12);
  const [expansionDuration, setExpansionDuration] = useState(14);
  const [timeHorizon, setTimeHorizon] = useState(30);
  const [state, setState] = useState<'idle' | 'running' | 'done'>('idle');
  const [saved, setSaved] = useState(false);

  const handleRun = async () => {
    setState('running');
    try {
      await api.runCapacitySimulation({ suiteCount, arrivalRate, qcFailRate, expansionDuration, timeHorizon });
    } catch { /* fall through to show mock results */ }
    setState('done');
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <AppShell currentUser="David M.">
      <h1 className="text-lg font-semibold text-neutral-900 mb-4">Capacity planning — What-if analysis</h1>

      <div className="grid grid-cols-[30%_70%] gap-6">
        {/* Left: Controls */}
        <div className="bg-white border border-neutral-200 rounded-lg p-5 h-fit">
          <h2 className="text-sm font-semibold text-neutral-800 mb-4">Scenario controls</h2>

          <div className="space-y-5">
            <div>
              <label className="flex items-center justify-between text-sm text-neutral-600 mb-1.5">
                <span>Number of suites</span>
                <span className="font-medium text-neutral-800">{suiteCount}</span>
              </label>
              <input type="range" min={4} max={12} value={suiteCount} onChange={(e) => setSuiteCount(+e.target.value)}
                className="w-full accent-primary" />
              <div className="flex justify-between text-[10px] text-neutral-400"><span>4</span><span>12</span></div>
            </div>

            <div>
              <label className="flex items-center justify-between text-sm text-neutral-600 mb-1.5">
                <span>Daily patient arrival rate</span>
                <span className="font-medium text-neutral-800">{arrivalRate}</span>
              </label>
              <input type="range" min={5} max={50} value={arrivalRate * 10} onChange={(e) => setArrivalRate(+e.target.value / 10)}
                className="w-full accent-primary" />
              <div className="flex justify-between text-[10px] text-neutral-400"><span>0.5</span><span>5.0</span></div>
            </div>

            <div>
              <label className="flex items-center justify-between text-sm text-neutral-600 mb-1.5">
                <span>QC failure rate</span>
                <span className="font-medium text-neutral-800">{qcFailRate}%</span>
              </label>
              <input type="range" min={5} max={25} value={qcFailRate} onChange={(e) => setQcFailRate(+e.target.value)}
                className="w-full accent-primary" />
              <div className="flex justify-between text-[10px] text-neutral-400"><span>5%</span><span>25%</span></div>
            </div>

            <div>
              <label className="flex items-center justify-between text-sm text-neutral-600 mb-1.5">
                <span>Avg expansion duration</span>
                <span className="font-medium text-neutral-800">{expansionDuration} days</span>
              </label>
              <input type="range" min={10} max={20} value={expansionDuration} onChange={(e) => setExpansionDuration(+e.target.value)}
                className="w-full accent-primary" />
              <div className="flex justify-between text-[10px] text-neutral-400"><span>10</span><span>20</span></div>
            </div>

            <div>
              <label className="text-sm text-neutral-600 mb-1.5 block">Time horizon</label>
              <select
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(+e.target.value)}
                className="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value={30}>30 days</option>
                <option value={60}>60 days</option>
                <option value={90}>90 days</option>
                <option value={180}>180 days</option>
              </select>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-neutral-100">
            <p className="text-xs text-neutral-400 mb-3">
              Simulation will run 1,000 trajectories. Estimated time: 12 seconds.
            </p>
            <button
              onClick={handleRun}
              disabled={state === 'running'}
              className="w-full flex items-center justify-center gap-2 bg-primary text-white font-medium py-2.5 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
            >
              {state === 'running' ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Running...</>
              ) : (
                <><PlayCircle className="w-4 h-4" /> Run simulation</>
              )}
            </button>
          </div>
        </div>

        {/* Right: Results */}
        <div>
          {state === 'idle' && (
            <div className="bg-white border border-neutral-200 rounded-lg p-12 flex items-center justify-center text-neutral-400 text-sm">
              Configure parameters and run a simulation to see results
            </div>
          )}

          {state === 'running' && (
            <div className="bg-white border border-neutral-200 rounded-lg p-12 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-neutral-500">Running 1,000 trajectories...</p>
            </div>
          )}

          {state === 'done' && (
            <div className="space-y-4">
              {/* Headline metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white border border-neutral-200 rounded-lg p-4">
                  <div className="text-xs text-neutral-400 uppercase tracking-wide">Projected throughput</div>
                  <div className="text-2xl font-semibold text-neutral-900">28 <span className="text-sm font-normal text-neutral-400">batches/week</span></div>
                  <div className="text-sm text-success font-medium">+27% vs current</div>
                </div>
                <div className="bg-white border border-neutral-200 rounded-lg p-4">
                  <div className="text-xs text-neutral-400 uppercase tracking-wide">Projected avg wait</div>
                  <div className="text-2xl font-semibold text-neutral-900">9.1 <span className="text-sm font-normal text-neutral-400">days</span></div>
                  <div className="text-sm text-success font-medium">-2.3 days vs current</div>
                </div>
                <div className="bg-white border border-neutral-200 rounded-lg p-4">
                  <div className="text-xs text-neutral-400 uppercase tracking-wide">Projected utilization</div>
                  <div className="text-2xl font-semibold text-neutral-900">72%</div>
                  <div className="text-sm text-warning font-medium">-9pp vs current</div>
                </div>
              </div>

              {/* Throughput chart */}
              <div className="bg-white border border-neutral-200 rounded-lg p-5">
                <h3 className="text-sm font-medium text-neutral-700 mb-4">Throughput projection</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <ComposedChart data={throughputSimData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                    <Area dataKey="upper" fill="#3b82f6" fillOpacity={0.08} stroke="none" />
                    <Area dataKey="lower" fill="#ffffff" stroke="none" />
                    <Line type="monotone" dataKey="current" stroke="#9ca3af" strokeWidth={1.5} dot={false} />
                    <Line type="monotone" dataKey="projected" stroke="#1e2761" strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
                <div className="flex items-center gap-4 mt-2 text-xs text-neutral-400">
                  <div className="flex items-center gap-1.5"><div className="w-4 h-0.5 bg-neutral-400" /><span>Current</span></div>
                  <div className="flex items-center gap-1.5"><div className="w-4 h-0.5 bg-primary" /><span>Projected</span></div>
                  <div className="flex items-center gap-1.5"><div className="w-4 h-2 bg-info/10 rounded-sm" /><span>Confidence band (5th–95th pctl)</span></div>
                </div>
              </div>

              {/* Bottleneck analysis */}
              <div className="bg-white border border-neutral-200 rounded-lg p-5">
                <h3 className="text-sm font-medium text-neutral-700 mb-4">Bottleneck analysis</h3>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={bottleneckData} layout="vertical" margin={{ left: 120 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                    <XAxis type="number" domain={[0, 50]} tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} width={120} />
                    <Bar dataKey="value" fill="#1e2761" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Bottom actions */}
              <div className="flex items-center gap-3">
                <button onClick={handleSave} className="flex items-center gap-1.5 border border-neutral-300 text-neutral-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-neutral-50">
                  {saved ? <CheckCircle className="w-4 h-4 text-success" /> : <Save className="w-4 h-4" />}
                  {saved ? 'Saved!' : 'Save scenario'}
                </button>
                <button onClick={() => alert('Compare view coming soon')} className="flex items-center gap-1.5 border border-neutral-300 text-neutral-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-neutral-50">
                  <GitCompare className="w-4 h-4" /> Compare scenarios
                </button>
                <button onClick={() => alert('Export coming soon')} className="flex items-center gap-1.5 border border-neutral-300 text-neutral-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-neutral-50">
                  <Download className="w-4 h-4" /> Export to slides
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
