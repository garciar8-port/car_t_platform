import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import ActionCard from '../components/ui/ActionCard';
import KpiTile from '../components/ui/KpiTile';
import { actionCards, batches, coordinatorKpis, suites } from '../data/mock';
import { RefreshCw, Filter } from 'lucide-react';
import type { BatchStatus } from '../types';

const batchStatusColors: Record<BatchStatus, string> = {
  in_progress: 'bg-accent text-white',
  scheduled: 'bg-info/20 text-info border border-info/30',
  at_risk: 'bg-warning/20 text-warning border border-warning/30',
  blocked: 'bg-danger/20 text-danger border border-danger/30',
  completed: 'bg-neutral-200 text-neutral-500',
};

type ViewRange = '24h' | '48h' | '7d';

export default function CoordinatorHomePage() {
  const [viewRange, setViewRange] = useState<ViewRange>('24h');
  const totalHours = viewRange === '24h' ? 24 : viewRange === '48h' ? 48 : 168;
  const currentHour = 8; // 8am

  return (
    <AppShell>
      <div className="grid grid-cols-[30%_45%_25%] gap-4 h-[calc(100vh-5rem)]">
        {/* Left: Needs your attention */}
        <div className="flex flex-col min-h-0">
          <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-3">
            Needs your attention
          </h2>
          <div className="flex flex-col gap-2 overflow-y-auto">
            {actionCards.map((card) => (
              <ActionCard key={card.id} {...card} />
            ))}
          </div>
        </div>

        {/* Center: Today's schedule (Gantt) */}
        <div className="flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide">
              Today's schedule
            </h2>
            <div className="flex items-center gap-2">
              {(['24h', '48h', '7d'] as ViewRange[]).map((range) => (
                <button
                  key={range}
                  onClick={() => setViewRange(range)}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                    viewRange === range
                      ? 'bg-primary text-white'
                      : 'text-neutral-500 hover:bg-neutral-100'
                  }`}
                >
                  {range}
                </button>
              ))}
              <button className="p-1.5 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded">
                <Filter className="w-3.5 h-3.5" />
              </button>
              <button className="flex items-center gap-1 text-xs text-neutral-400 hover:text-neutral-600 p-1.5 hover:bg-neutral-100 rounded">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
          <div className="text-[10px] text-neutral-400 mb-1 text-right">Last updated: 8:02am</div>

          {/* Gantt Chart */}
          <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden flex-1 min-h-0">
            {/* Time axis */}
            <div className="flex border-b border-neutral-100 px-2 py-1.5 text-[10px] text-neutral-400">
              <div className="w-16 shrink-0" />
              <div className="flex-1 flex relative">
                {Array.from({ length: Math.min(totalHours / (viewRange === '7d' ? 24 : 1), 24) }, (_, i) => {
                  const hour = viewRange === '7d' ? i : i;
                  const label = viewRange === '7d' ? `Day ${i + 1}` : `${(hour) % 24}:00`;
                  return (
                    <div key={i} className="flex-1 text-center truncate">{label}</div>
                  );
                })}
              </div>
            </div>

            {/* Suite lanes */}
            <div className="overflow-y-auto">
              {suites.map((suite) => {
                const suiteBatches = batches.filter((b) => b.suiteId === suite.id);
                return (
                  <div key={suite.id} className="flex items-center border-b border-neutral-50 hover:bg-neutral-50/50">
                    <div className="w-16 shrink-0 px-2 py-3">
                      <div className="text-xs font-medium text-neutral-700">{suite.name}</div>
                      <div className="text-[10px] text-neutral-400 capitalize">{suite.status.replace('_', ' ')}</div>
                    </div>
                    <div className="flex-1 relative h-12 py-1.5">
                      {/* Current time indicator */}
                      <div
                        className="absolute top-0 bottom-0 w-px bg-danger/40 z-10"
                        style={{ left: `${(currentHour / totalHours) * 100}%` }}
                      >
                        <div className="w-1.5 h-1.5 bg-danger rounded-full -translate-x-[2.5px] -translate-y-0.5" />
                      </div>

                      {suiteBatches.map((batch) => {
                        const left = (batch.startHour / totalHours) * 100;
                        const width = (batch.durationHours / totalHours) * 100;
                        return (
                          <div
                            key={batch.id}
                            className={`absolute top-1.5 bottom-1.5 rounded text-[9px] font-medium px-1.5 flex items-center overflow-hidden cursor-pointer hover:opacity-90 ${batchStatusColors[batch.status]}`}
                            style={{ left: `${left}%`, width: `${width}%`, minWidth: '40px' }}
                            title={`${batch.id} · ${batch.patientId} · ${batch.phase}`}
                          >
                            <span className="truncate">{batch.patientId} · {batch.phase}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: At a glance */}
        <div className="flex flex-col gap-3 min-h-0">
          <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide">
            At a glance
          </h2>
          <div className="flex flex-col gap-2 overflow-y-auto">
            {coordinatorKpis.map((kpi) => (
              <KpiTile key={kpi.label} {...kpi} />
            ))}

            {/* System status */}
            <div className="bg-white border border-neutral-200 rounded-lg p-3 mt-1">
              <div className="text-[10px] font-medium text-neutral-400 uppercase tracking-wide mb-2">System status</div>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-1.5 h-1.5 bg-success rounded-full" />
                <span className="text-xs text-neutral-600">Model v2.3.1</span>
              </div>
              <div className="text-[10px] text-neutral-400">Trained 2 weeks ago · Avg confidence 87%</div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
