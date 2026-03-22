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

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id} className="pointer-events-auto animate-slide-in-right flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg max-w-sm"
            style={{ background: t.type === "success" ? "rgba(34,197,94,0.12)" : t.type === "warning" ? "rgba(245,158,11,0.12)" : "rgba(99,102,241,0.12)",
              border: `1px solid ${t.type === "success" ? "rgba(34,197,94,0.3)" : t.type === "warning" ? "rgba(245,158,11,0.3)" : "rgba(99,102,241,0.3)"}` }}>
            {t.type === "success" ? <CheckCircle size={18} className="text-green-400 shrink-0 mt-0.5" /> : <AlertTriangle size={18} className="text-amber-400 shrink-0 mt-0.5" />}
            <p className="text-sm text-slate-200 flex-1">{t.message}</p>
            <button onClick={() => dismiss(t.id)} className="text-slate-400 hover:text-slate-200 shrink-0"><X size={14} /></button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx.toast;
}
