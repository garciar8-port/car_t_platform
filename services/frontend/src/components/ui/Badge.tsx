interface BadgeProps {
  variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  children: React.ReactNode;
}

const variantClasses: Record<BadgeProps['variant'], string> = {
  success: 'bg-success/10 text-success border-success/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  danger: 'bg-danger/10 text-danger border-danger/20',
  info: 'bg-info/10 text-info border-info/20',
  neutral: 'bg-neutral-100 text-neutral-500 border-neutral-200',
};

export default function Badge({ variant, children }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantClasses[variant]}`}>
      {children}
    </span>
  );
}
