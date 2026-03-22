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

export function Button({
  variant = "primary",
  size = "md",
  loading,
  children,
  fullWidth,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 font-semibold rounded-[12px] transition-all duration-150 select-none";

  const sizes = {
    sm: "px-4 py-2 text-sm min-h-[36px]",
    md: "px-6 py-3 text-sm min-h-[44px]",
    lg: "px-6 py-3 text-base min-h-[52px]",
  };

  const variants = {
    primary:
      "bg-[#C9A84C] text-[#0F1F3D] hover:scale-[1.02] active:scale-[0.98]",
    secondary:
      "bg-transparent border-[1.5px] border-[#0F1F3D] text-[#0F1F3D] hover:bg-[#0F1F3D]/5",
    ghost:
      "bg-transparent text-[#4A5568] hover:bg-[#0F1F3D]/6 hover:text-[#0F1F3D]",
    destructive:
      "bg-transparent border-[1.5px] border-amber-600/40 text-amber-700 hover:bg-amber-50",
  };

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={clsx(
        base,
        sizes[size],
        variants[variant],
        fullWidth && "w-full",
        (disabled || loading) && "opacity-40 cursor-not-allowed hover:scale-100",
        className
      )}
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
