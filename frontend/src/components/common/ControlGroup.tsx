export interface ControlGroupProps {
  label: string;
  children: React.ReactNode;
  error?: string;
  className?: string;
}

export function ControlGroup({ label, children, error, className }: ControlGroupProps) {
  return (
    <div className={className}>
      <label className="block text-sm font-bold mb-2 uppercase tracking-wide">
        {label}
        {error && <span className="text-red-600 ml-2">•</span>}
      </label>
      <div className={error ? 'border-2 border-red-600' : ''}>{children}</div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
