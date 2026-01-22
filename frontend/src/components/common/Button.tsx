import { cn } from '../../lib/utils';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'danger';
export type ButtonSize = 'xs' | 'sm' | 'md';

export interface ButtonProps {
  children: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  className?: string;
  ariaLabel?: string;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  type = 'button',
  leftIcon,
  rightIcon,
  className,
  ariaLabel,
}: ButtonProps) {
  const variantClasses = {
    primary:
      'bg-primary border-black text-black hover:bg-primary-dark hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,0.8)]',
    secondary:
      'bg-gray-200 border-gray-400 text-gray-700 hover:bg-gray-300',
    outline:
      'bg-white border-black text-black hover:bg-gray-100',
    danger:
      'bg-red-100 border-red-500 text-red-700 hover:bg-red-200',
  };

  const sizeClasses = {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
  };

  return (
    <button
      type={type}
      aria-label={ariaLabel}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-bold uppercase tracking-wide border-2 cursor-pointer',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {leftIcon}
      {children}
      {rightIcon}
    </button>
  );
}
