"use client";
import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { CheckCircle, AlertTriangle, X } from "lucide-react";

type ToastType = "success" | "warning" | "info";
interface Toast { id: string; message: string; type: ToastType; }

interface ToastCtx { toast: (msg: string, type?: ToastType) => void; }
const ToastContext = createContext<ToastCtx | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: ToastType = "success") => {
    const id = Math.random().toString(36).slice(2);
    setToasts(p => [...p, { id, message, type }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
  }, []);

  const dismiss = (id: string) => setToasts(p => p.filter(t => t.id !== id));

  const styles: Record<ToastType, { bg: string; border: string; icon: string }> = {
    success: { bg: "rgba(26,107,58,0.06)",  border: "rgba(26,107,58,0.20)",  icon: "#1A6B3A" },
    warning: { bg: "rgba(180,130,0,0.06)",  border: "rgba(180,130,0,0.22)",  icon: "#92660A" },
    info:    { bg: "rgba(15,31,61,0.04)",   border: "rgba(15,31,61,0.14)",   icon: "#0F1F3D" },
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
        {toasts.map(t => {
          const s = styles[t.type];
          return (
            <div
              key={t.id}
              className="pointer-events-auto animate-slide-in-right flex items-start gap-3 px-4 py-3 rounded-[12px] max-w-sm bg-white"
              style={{
                border: `1px solid ${s.border}`,
                boxShadow: "0 4px 16px rgba(15,31,61,0.10)",
              }}
            >
              {t.type === "success"
                ? <CheckCircle size={17} style={{ color: s.icon }} className="shrink-0 mt-0.5" />
                : <AlertTriangle size={17} style={{ color: s.icon }} className="shrink-0 mt-0.5" />
              }
              <p className="text-sm text-[#0F1F3D] flex-1 leading-relaxed">{t.message}</p>
              <button onClick={() => dismiss(t.id)} className="text-[#718096] hover:text-[#0F1F3D] shrink-0 transition-colors">
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx.toast;
}
