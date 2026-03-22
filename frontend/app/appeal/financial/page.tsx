"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, TrendingDown, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Nav } from "@/components/layout/Nav";
import { SkeletonCard } from "@/components/ui/Skeleton";
import api from "@/lib/api";

interface Scenario { label: string; description: string; total_12m_cost: number; final_balance: number; trajectory: { month: number; balance: number }[]; color: string; }
interface SimResult { scenarios: Record<"A"|"B"|"C", Scenario>; summary: { best_case_savings: number; monthly_patient_cost: number; er_visit_cost: number }; procedure_cost: number; }

function MiniChart({ trajectory, color }: { trajectory: { month: number; balance: number }[]; color: string }) {
  const values = trajectory.map(t => t.balance);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const w = 200, h = 60, pad = 4;
  const pts = values.map((v, i) => `${pad + (i / (values.length - 1)) * (w - pad * 2)},${pad + (1 - (v - min) / range) * (h - pad * 2)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function FinancialPage() {
  const router = useRouter();
  const toast = useToast();
  const { denial, cptCode } = useVinci();
  const [data, setData] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!cptCode && !denial) return;
    setLoading(true);
    api.post("/api/financial/simulate", {
      cpt_code: cptCode || "99214",
      deductible_remaining: 2000,
      oop_max: 6000,
      plan_type: "PPO",
    }).then(r => setData(r.data)).catch(() => toast("This is taking longer than usual. We're still working on it.", "warning"))
      .finally(() => setLoading(false));
  }, [cptCode, denial]);

  const fmtDollar = (n: number) => `$${n.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

  const scenarioMeta = {
    A: { icon: CheckCircle, badge: "Recommended", goldBorder: true },
    B: { icon: TrendingDown, badge: null,          goldBorder: false },
    C: { icon: AlertTriangle, badge: null,         goldBorder: false },
  };

  return (
    <div className="min-h-screen bg-slate-950">
      <Nav />
      <div className="pt-20 pb-16 px-4 max-w-5xl mx-auto">
        <div className="mb-10">
          <h1 className="text-3xl font-bold mb-2">Here's what this denial is actually costing you</h1>
          <p className="text-slate-400">Three paths forward. One obvious choice.</p>
        </div>

        {loading && <div className="grid grid-cols-1 sm:grid-cols-3 gap-5"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>}

        {data && !loading && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
              {(["A", "B", "C"] as const).map(key => {
                const s = data.scenarios[key];
                const { icon: Icon, badge, goldBorder } = scenarioMeta[key];
                return (
                  <div key={key} className={`bg-slate-900 rounded-2xl p-6 flex flex-col gap-4 border-2 transition-all ${goldBorder ? "border-[#C9A84C]" : "border-slate-800"}`}>
                    {badge && (
                      <span className="self-start px-3 py-1 rounded-full text-xs font-semibold bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/25">
                        {badge}
                      </span>
                    )}
                    <div>
                      <p className="text-4xl font-bold mb-1" style={{ color: s.color }}>
                        {fmtDollar(s.total_12m_cost)}{key === "C" && "+"}
                      </p>
                      <p className="text-xs text-slate-500 uppercase tracking-wide">
                        {key === "A" ? "Additional out-of-pocket cost" : key === "B" ? "Cost over 12 months" : "Average ER visit cost"}
                      </p>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed flex-1">{s.description}</p>
                    {key !== "A" && (
                      <div className="mt-auto">
                        <p className="text-xs text-slate-600 mb-1">12-month balance trajectory</p>
                        <MiniChart trajectory={s.trajectory} color={s.color} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <p className="text-center text-slate-400 text-sm mb-8 italic">
              "The appeal takes 60 seconds. The savings are real. The choice is easy."
            </p>

            <div className="bg-slate-900/60 border border-[#C9A84C]/20 rounded-2xl p-5 flex items-center justify-between mb-8">
              <div>
                <p className="text-sm text-slate-400">Appealing saves you up to</p>
                <p className="text-2xl font-bold text-[#C9A84C]">{fmtDollar(data.summary.best_case_savings)}</p>
              </div>
              <CheckCircle size={32} className="text-[#C9A84C]" />
            </div>

            <Button size="lg" fullWidth onClick={() => router.push("/appeal/rights")}>
              See your rights and deadlines <ArrowRight size={18} />
            </Button>
          </>
        )}

        {!loading && !data && (
          <div className="text-center py-16 text-slate-500">
            <p className="mb-4">Upload a denial letter first to see your financial simulation.</p>
            <Button variant="secondary" onClick={() => router.push("/denial")}>Upload denial letter</Button>
          </div>
        )}
      </div>
    </div>
  );
}
