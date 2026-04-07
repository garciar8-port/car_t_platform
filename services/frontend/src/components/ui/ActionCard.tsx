import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import type { ActionCardType } from '../../types';
import { Link } from 'react-router-dom';

interface ActionCardProps {
  type: ActionCardType;
  description: string;
  timeSinceFlag: string;
  action: string;
  link: string;
}

const config: Record<ActionCardType, { icon: typeof AlertCircle; border: string; iconColor: string; bg: string }> = {
  urgent: { icon: AlertCircle, border: 'border-l-danger', iconColor: 'text-danger', bg: 'bg-danger/5' },
  attention: { icon: AlertTriangle, border: 'border-l-warning', iconColor: 'text-warning', bg: 'bg-warning/5' },
  info: { icon: Info, border: 'border-l-info', iconColor: 'text-info', bg: 'bg-white' },
};

export default function ActionCard({ type, description, timeSinceFlag, action, link }: ActionCardProps) {
  const { icon: Icon, border, iconColor, bg } = config[type];

  return (
    <div className={`${bg} border border-neutral-200 border-l-4 ${border} rounded-lg p-3`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${iconColor}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-neutral-800 leading-snug">{description}</p>
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-neutral-400">{timeSinceFlag}</span>
            <Link
              to={link}
              className="text-xs font-medium text-primary hover:text-primary/80 bg-primary/5 px-3 py-1 rounded"
            >
              {action}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
