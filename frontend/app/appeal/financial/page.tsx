"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle, AlertTriangle } from "lucide-react";
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

const cardBase = {
  background: "#FFFFFF",
  borderRadius: "16px",
  boxShadow: "0 2px 8px rgba(15,31,61,0.06)",
  transition: "box-shadow 200ms ease, transform 200ms ease",
};

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

  return (
    <div className="min-h-screen" style={{ background: "var(--warm-white)" }}>
      <Nav />
      <div className="pt-24 pb-20 px-6 max-w-[1200px] mx-auto">

        <div className="mb-12 animate-fade-in-up" style={{ maxWidth: "600px" }}>
          <h1 style={{ color: "var(--text-primary)", marginBottom: "0.75rem" }}>
            Here's what this denial is actually costing you
          </h1>
          <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
            Three paths forward. One obvious choice.
          </p>
        </div>

        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <SkeletonCard /><SkeletonCard /><SkeletonCard />
          </div>
        )}

        {data && !loading && (
          <>
            {/* Scenario cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
              {(["A", "B", "C"] as const).map((key, i) => {
                const s = data.scenarios[key];
                const isRecommended = key === "A";
                return (
                  <div key={key}
                    className={`p-8 flex flex-col gap-5 animate-fade-in-up stagger-${i + 1}`}
                    style={{
                      ...cardBase,
                      border: isRecommended
                        ? "2px solid var(--gold)"
                        : "1px solid rgba(15,31,61,0.06)",
                    }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.boxShadow = "0 8px 24px rgba(15,31,61,0.10)";
                      (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 8px rgba(15,31,61,0.06)";
                      (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
                    }}
                  >
                    {isRecommended && (
                      <span className="self-start px-3 py-1 rounded-full text-xs font-medium"
                        style={{ background: "var(--gold-light)", color: "var(--gold)", border: "1px solid var(--gold-border)", fontFamily: "var(--font-inter)", letterSpacing: "0.02em" }}>
                        Recommended
                      </span>
                    )}

                    <div>
                      <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 800, fontSize: "2.25rem", color: s.color, letterSpacing: "-0.03em", lineHeight: 1 }}>
                        {fmtDollar(s.total_12m_cost)}{key === "C" && "+"}
                      </p>
                      <p className="mt-1" style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                        {key === "A" ? "Additional out-of-pocket cost" : key === "B" ? "Cost over 12 months" : "Average ER visit cost"}
                      </p>
                    </div>

                    <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.65, flex: 1 }}>
                      {s.description}
                    </p>

                    {key !== "A" && (
                      <div className="mt-auto">
                        <p style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginBottom: "0.375rem" }}>
                          12-month balance trajectory
                        </p>
                        <MiniChart trajectory={s.trajectory} color={s.color} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Quote */}
            <p className="text-center mb-8 animate-fade-in-up"
              style={{ fontSize: "0.9rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontStyle: "italic" }}>
              "The appeal takes 60 seconds. The savings are real. The choice is easy."
            </p>

            {/* Savings banner */}
            <div className="flex items-center justify-between p-6 rounded-[16px] mb-8 animate-fade-in-up"
              style={{ background: "var(--gold-light)", border: "1px solid var(--gold-border)" }}>
              <div>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", marginBottom: "0.25rem" }}>
                  Appealing saves you up to
                </p>
                <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 800, fontSize: "2rem", color: "var(--gold)", letterSpacing: "-0.03em" }}>
                  {fmtDollar(data.summary.best_case_savings)}
                </p>
              </div>
              <CheckCircle size={32} style={{ color: "var(--gold)" }} />
            </div>

            <Button size="lg" fullWidth onClick={() => router.push("/appeal/rights")}>
              See your rights and deadlines <ArrowRight size={18} />
            </Button>
          </>
        )}

        {!loading && !data && (
          <div className="text-center py-20 animate-fade-in-up">
            <p style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginBottom: "1.5rem" }}>
              Upload a denial letter first to see your financial simulation.
            </p>
            <Button variant="secondary" onClick={() => router.push("/denial")}>Upload denial letter</Button>
          </div>
        )}
      </div>
    </div>
  );
}
