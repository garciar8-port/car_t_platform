import type { KpiData } from '../../types';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KpiTileProps extends KpiData {
  large?: boolean;
}

export default function KpiTile({ label, value, unit, delta, deltaDirection, target, status, large }: KpiTileProps) {
  const statusDot = {
    good: 'bg-success',
    warning: 'bg-warning',
    danger: 'bg-danger',
  };

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">{label}</span>
        <span className={`w-2 h-2 rounded-full ${statusDot[status]}`} />
      </div>
      <div className={`font-semibold text-neutral-900 ${large ? 'text-3xl' : 'text-2xl'}`}>
        {value}
        {unit && <span className="text-sm font-normal text-neutral-400 ml-1">{unit}</span>}
      </div>
      {target && (
        <div className="text-xs text-neutral-400 mt-1">{target}</div>
      )}
      {delta && (
        <div className={`flex items-center gap-1 text-xs mt-1 ${
          deltaDirection === 'down' ? 'text-success' : deltaDirection === 'up' ? 'text-danger' : 'text-neutral-500'
        }`}>
          {deltaDirection === 'down' && <TrendingDown className="w-3 h-3" />}
          {deltaDirection === 'up' && <TrendingUp className="w-3 h-3" />}
          {delta}
        </div>
      )}
    </div>
  );
}
