interface ConfidencePillProps {
  confidence: number;
  size?: 'sm' | 'lg';
}

export default function ConfidencePill({ confidence, size = 'sm' }: ConfidencePillProps) {
  const variant = confidence >= 85 ? 'success' : confidence >= 70 ? 'warning' : 'danger';
  const colors = {
    success: 'bg-success/10 text-success border-success/30',
    warning: 'bg-warning/10 text-warning border-warning/30',
    danger: 'bg-danger/10 text-danger border-danger/30',
  };
  const sizes = {
    sm: 'px-2.5 py-0.5 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  };

  return (
    <span className={`inline-flex items-center rounded-full font-semibold border ${colors[variant]} ${sizes[size]}`}>
      {confidence}% confidence
    </span>
  );
}
