"use client";
import { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: ReactNode;
  fullWidth?: boolean;
}

export function Button({ variant = "primary", size = "md", loading, children, fullWidth, className, disabled, ...props }: ButtonProps) {
  const base = "inline-flex items-center justify-center gap-2 font-semibold rounded-xl transition-all duration-150 select-none";
  const sizes = { sm: "px-4 py-2 text-sm min-h-[36px]", md: "px-5 py-2.5 text-sm min-h-[44px]", lg: "px-6 py-3 text-base min-h-[52px]" };
  const variants = {
    primary:     "bg-[#C9A84C] text-[#0F1F3D] hover:scale-[1.02] hover:bg-[#E4C97A] active:scale-[0.98] shadow-sm",
    secondary:   "bg-transparent border border-slate-600 text-slate-200 hover:border-slate-400 hover:bg-slate-800/50",
    ghost:       "bg-transparent text-slate-300 hover:bg-slate-800/60 hover:text-slate-100",
    destructive: "bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20",
  };

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={clsx(base, sizes[size], variants[variant], fullWidth && "w-full", (disabled || loading) && "opacity-50 cursor-not-allowed hover:scale-100", className)}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          {typeof children === "string" ? children : "Loading…"}
        </span>
      ) : children}
    </button>
  );
}
