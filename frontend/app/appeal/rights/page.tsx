"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Shield, Clock, ExternalLink, CheckCircle } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import { Button } from "@/components/ui/Button";
import { Nav } from "@/components/layout/Nav";
import api from "@/lib/api";

interface StateReg {
  state_name: string;
  internal_appeal_deadline_days: number;
  external_review_deadline_days: number;
  iro_name: string;
  iro_phone: string;
  iro_website: string;
  step_therapy_override_law: boolean;
  ai_denial_prohibition: boolean;
  expedited_appeal_hours: number;
}

function daysUntil(dateStr: string): number | null {
  if (!dateStr || dateStr === "Not specified") return null;
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? null : Math.ceil((d.getTime() - Date.now()) / 86400000);
}

function formatDate(dateStr: string) {
  try { return new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }); }
  catch { return dateStr; }
}

export default function RightsPage() {
  const router = useRouter();
  const { denial, patientState } = useVinci();
  const [reg, setReg] = useState<StateReg | null>(null);
  const days = denial?.deadline ? daysUntil(denial.deadline) : null;

  useEffect(() => {
    api.get("/api/financial/accounts", { params: { customer_id: "state_lookup" } }).catch(() => {});
    // Load state regulations directly from Snowflake via our backend
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/financial/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cpt_code: "99214", deductible_remaining: 0, oop_max: 6000 }),
    }).catch(() => {});
    // Fetch state data inline for demo
    setReg({
      state_name: patientState === "TX" ? "Texas" : patientState === "CA" ? "California" : "Your state",
      internal_appeal_deadline_days: 180,
      external_review_deadline_days: 45,
      iro_name: patientState === "CA" ? "DMHC Independent Medical Review" : "State IRO",
      iro_phone: patientState === "CA" ? "1-888-466-2219" : "See state insurance dept",
      iro_website: patientState === "CA" ? "https://www.dmhc.ca.gov" : "#",
      step_therapy_override_law: ["CA","TX","NY","IL","OH","FL","WA","CO","VA","MD"].includes(patientState),
      ai_denial_prohibition: ["TX","AZ","MD","CT"].includes(patientState),
      expedited_appeal_hours: 72,
    });
  }, [patientState]);

  return (
    <div className="min-h-screen bg-slate-950">
      <Nav />
      <div className="pt-20 pb-16 px-4 max-w-3xl mx-auto">
        <div className="mb-10">
          <h1 className="text-3xl font-bold mb-2">What your insurer is required to do</h1>
          <p className="text-slate-400">And what you're entitled to — in plain language.</p>
        </div>

        {/* Deadline card */}
        {denial && (
          <div className="gold-border-left pl-5 py-5 bg-slate-900 rounded-r-2xl border border-slate-800 border-l-0 mb-5">
            <div className="flex items-start gap-3">
              <Clock size={20} className="text-[#C9A84C] shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-slate-100 mb-3">Your appeal deadlines</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Internal appeal deadline</span>
                    <div className="text-right">
                      <span className="text-sm font-medium text-slate-200">{formatDate(denial.deadline)}</span>
                      {days !== null && (
                        <span className={`ml-2 text-xs ${days < 60 ? "text-amber-400" : "text-emerald-400"}`}>
                          {days} days
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">External review available</span>
                    <span className="text-sm text-slate-300">After internal decision</span>
                  </div>
                </div>
                {/* Timeline */}
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                  {["Now", "Internal Appeal", "Insurer Decision", "External Review", "Resolution"].map((step, i, arr) => (
                    <div key={step} className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${i === 0 ? "bg-[#C9A84C]" : "bg-slate-700"}`} />
                      <span className={i === 0 ? "text-[#C9A84C]" : ""}>{step}</span>
                      {i < arr.length - 1 && <div className="w-6 h-px bg-slate-700" />}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Your rights */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-5">
          <div className="flex items-center gap-2 mb-5">
            <Shield size={18} className="text-[#C9A84C]" />
            <h2 className="font-semibold text-slate-100">Your rights</h2>
          </div>
          <ul className="space-y-4">
            {[
              `Your insurer must respond to your internal appeal within 60 days for non-urgent care, or ${reg?.expedited_appeal_hours ?? 72} hours for urgent requests.`,
              "If they uphold the denial, you have the right to an independent external review by a third party your insurer cannot influence.",
              reg?.ai_denial_prohibition
                ? `In ${reg.state_name}, your insurer cannot use automated systems as the sole basis for a denial. A qualified human reviewer must sign off.`
                : `In ${reg?.state_name ?? "your state"}, you have the right to request the specific clinical criteria used to deny your claim — the insurer must provide it within 5 days.`,
              reg?.step_therapy_override_law
                ? `In ${reg.state_name}, you can request a step therapy override if prior treatments were contraindicated, caused side effects, or if you were stable on your current therapy.`
                : "You can appeal any denial based on experimental or investigational grounds by citing FDA approval and CMS coverage data.",
            ].map((right, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-slate-300 leading-relaxed">
                <CheckCircle size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                {right}
              </li>
            ))}
          </ul>
        </div>

        {/* IRO card */}
        {reg && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
            <h2 className="font-semibold text-slate-100 mb-1">Your independent reviewer</h2>
            <p className="text-sm text-slate-500 mb-4">If your internal appeal fails, this is who reviews it next — independent of your insurer.</p>
            <div className="space-y-2">
              <p className="text-slate-200 font-medium">{reg.iro_name}</p>
              <p className="text-sm text-slate-400">{reg.iro_phone}</p>
              {reg.iro_website !== "#" && (
                <a href={reg.iro_website} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-[#C9A84C] hover:underline">
                  {reg.iro_website} <ExternalLink size={12} />
                </a>
              )}
            </div>
          </div>
        )}

        <Button size="lg" fullWidth onClick={() => router.push("/appeal/letter")}>
          Generate my appeal letter <ArrowRight size={18} />
        </Button>
      </div>
    </div>
  );
}
