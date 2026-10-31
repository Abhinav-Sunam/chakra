import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// -----------------------------------------------------------------------------
// Base Card & Panel
// -----------------------------------------------------------------------------
export interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'glass';
  glow?: boolean;
}

export const Panel = React.forwardRef<HTMLDivElement, PanelProps>(
  ({ className, variant = 'default', glow = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl border transition-all duration-150',
          variant === 'default' && 'bg-panel/95 border-border backdrop-blur-md glow-panel',
          variant === 'elevated' && 'bg-panel2 border-border shadow-xl',
          variant === 'glass' && 'bg-panel/80 border-border/80 backdrop-blur-lg',
          glow && 'shadow-[0_0_20px_rgba(79,195,217,0.15)] border-teal/40',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Panel.displayName = 'Panel';

export const Card = React.forwardRef<HTMLDivElement, PanelProps>(
  ({ className, variant = 'elevated', children, ...props }, ref) => {
    return (
      <Panel
        ref={ref}
        variant={variant}
        className={cn('p-3.5 space-y-2', className)}
        {...props}
      >
        {children}
      </Panel>
    );
  }
);
Card.displayName = 'Card';

// -----------------------------------------------------------------------------
// Stat Display
// -----------------------------------------------------------------------------
export interface StatProps {
  label: string;
  value: React.ReactNode;
  unit?: string;
  delta?: string | number;
  deltaType?: 'positive' | 'negative' | 'neutral';
  subtext?: string;
  className?: string;
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  unit,
  delta,
  deltaType = 'neutral',
  subtext,
  className,
}) => {
  return (
    <div className={cn('flex flex-col space-y-0.5', className)}>
      <span className="text-[11px] font-medium uppercase tracking-wider text-muted">
        {label}
      </span>
      <div className="flex items-baseline space-x-1.5">
        <span className="text-xl font-bold tracking-tight text-text tabular-nums">
          {value}
        </span>
        {unit && <span className="text-xs font-mono text-muted">{unit}</span>}
        {delta !== undefined && (
          <span
            className={cn(
              'text-[10px] font-mono px-1 rounded',
              deltaType === 'positive' && 'text-ok bg-ok/10',
              deltaType === 'negative' && 'text-crit bg-crit/10',
              deltaType === 'neutral' && 'text-muted bg-white/5'
            )}
          >
            {delta}
          </span>
        )}
      </div>
      {subtext && <span className="text-[10px] text-muted truncate">{subtext}</span>}
    </div>
  );
};

// -----------------------------------------------------------------------------
// Badges
// -----------------------------------------------------------------------------
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'teal' | 'orange' | 'ok' | 'warn' | 'crit';
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  pulse = false,
  className,
  ...props
}) => {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-wide border uppercase',
        variant === 'default' && 'bg-panel2 text-text border-border',
        variant === 'teal' && 'bg-teal/15 text-teal-bright border-teal/40',
        variant === 'orange' && 'bg-orange/15 text-orange border-orange/40',
        variant === 'ok' && 'bg-ok/15 text-ok border-ok/40',
        variant === 'warn' && 'bg-warn/15 text-warn border-warn/40',
        variant === 'crit' && 'bg-crit/15 text-crit border-crit/40',
        className
      )}
      {...props}
    >
      {pulse && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full animate-ping mr-0.5',
            variant === 'ok' && 'bg-ok',
            variant === 'warn' && 'bg-warn',
            variant === 'crit' && 'bg-crit',
            variant === 'teal' && 'bg-teal-bright',
            variant === 'orange' && 'bg-orange',
            variant === 'default' && 'bg-muted'
          )}
        />
      )}
      {children}
    </span>
  );
};

// -----------------------------------------------------------------------------
// Button & IconButton
// -----------------------------------------------------------------------------
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'secondary', size = 'md', isLoading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-teal-bright/40 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98]',
          size === 'sm' && 'text-xs px-2.5 py-1 gap-1.5',
          size === 'md' && 'text-xs px-3.5 py-1.5 gap-2',
          size === 'lg' && 'text-sm px-4 py-2 gap-2.5',
          variant === 'primary' &&
            'bg-teal hover:bg-teal-bright text-bg font-semibold shadow-md shadow-teal/20',
          variant === 'secondary' &&
            'bg-panel2 hover:bg-white/10 text-text border border-border',
          variant === 'ghost' &&
            'bg-transparent hover:bg-white/5 text-muted hover:text-text',
          variant === 'danger' &&
            'bg-crit/15 hover:bg-crit/25 text-crit border border-crit/30',
          className
        )}
        {...props}
      >
        {isLoading && (
          <span className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin mr-1" />
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  tooltip?: string;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, variant = 'ghost', size = 'md', tooltip, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        title={tooltip}
        className={cn(
          'inline-flex items-center justify-center rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-teal-bright/40 disabled:opacity-50 select-none active:scale-[0.96]',
          size === 'sm' && 'w-7 h-7 p-1 text-xs',
          size === 'md' && 'w-8 h-8 p-1.5 text-sm',
          size === 'lg' && 'w-10 h-10 p-2 text-base',
          variant === 'ghost' && 'text-muted hover:text-text hover:bg-white/10',
          variant === 'secondary' && 'bg-panel2 hover:bg-white/10 text-text border border-border',
          variant === 'primary' && 'bg-teal hover:bg-teal-bright text-bg',
          variant === 'danger' && 'text-crit hover:bg-crit/10 hover:border-crit/30',
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
IconButton.displayName = 'IconButton';

// -----------------------------------------------------------------------------
// Tabs & SegmentedControl
// -----------------------------------------------------------------------------
export interface SegmentedControlProps<T extends string> {
  options: { value: T; label: React.ReactNode }[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
  className?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  size = 'sm',
  className,
}: SegmentedControlProps<T>) {
  return (
    <div
      className={cn(
        'inline-flex p-0.5 rounded-lg bg-panel2/80 border border-border/80 text-xs font-medium',
        className
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              'rounded-md transition-all select-none',
              size === 'sm' && 'px-2.5 py-1 text-xs',
              size === 'md' && 'px-3.5 py-1.5 text-sm',
              active
                ? 'bg-panel text-teal-bright border border-border shadow-sm font-semibold'
                : 'text-muted hover:text-text hover:bg-white/5'
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

// -----------------------------------------------------------------------------
// Slider
// -----------------------------------------------------------------------------
export interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  valueDisplay?: React.ReactNode;
}

export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ label, valueDisplay, className, ...props }, ref) => {
    return (
      <div className="space-y-1">
        {(label || valueDisplay) && (
          <div className="flex items-center justify-between text-xs">
            {label && <span className="text-muted font-medium">{label}</span>}
            {valueDisplay && <span className="font-mono text-teal-bright tabular-nums">{valueDisplay}</span>}
          </div>
        )}
        <input
          ref={ref}
          type="range"
          className={cn(
            'w-full h-1.5 bg-panel2 rounded-lg appearance-none cursor-pointer accent-teal-bright border border-border/50 focus:outline-none focus:ring-1 focus:ring-teal-bright',
            className
          )}
          {...props}
        />
      </div>
    );
  }
);
Slider.displayName = 'Slider';

// -----------------------------------------------------------------------------
// Toggle
// -----------------------------------------------------------------------------
export interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
}) => {
  return (
    <label className={cn('flex items-center justify-between gap-3 cursor-pointer select-none', disabled && 'opacity-50 cursor-not-allowed')}>
      {(label || description) && (
        <div className="flex flex-col">
          {label && <span className="text-xs font-medium text-text">{label}</span>}
          {description && <span className="text-[10px] text-muted">{description}</span>}
        </div>
      )}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={cn(
          'relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-teal-bright/40',
          checked ? 'bg-teal' : 'bg-panel2 border-border'
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out',
            checked ? 'translate-x-4' : 'translate-x-0'
          )}
        />
      </button>
    </label>
  );
};

// -----------------------------------------------------------------------------
// Divider & Keyboard Key (Kbd)
// -----------------------------------------------------------------------------
export const Divider: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('h-px w-full bg-border my-2', className)} />
);

export const Kbd: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-panel2 border border-border rounded text-muted shadow-inner">
    {children}
  </kbd>
);
