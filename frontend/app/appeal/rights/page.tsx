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

const card = {
  background: "#FFFFFF",
  border: "1px solid rgba(15,31,61,0.06)",
  borderRadius: "16px",
  boxShadow: "0 2px 8px rgba(15,31,61,0.06)",
};

export default function RightsPage() {
  const router = useRouter();
  const { denial, patientState } = useVinci();
  const [reg, setReg] = useState<StateReg | null>(null);
  const days = denial?.deadline ? daysUntil(denial.deadline) : null;

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/financial/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cpt_code: "99214", deductible_remaining: 0, oop_max: 6000 }),
    }).catch(() => {});
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
    <div className="min-h-screen" style={{ background: "var(--warm-white)" }}>
      <Nav />
      <div className="pt-24 pb-20 px-6 max-w-3xl mx-auto">

        <div className="mb-12 animate-fade-in-up">
          <h1 style={{ color: "var(--text-primary)", marginBottom: "0.75rem" }}>
            What your insurer is required to do
          </h1>
          <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)", maxWidth: "50ch" }}>
            And what you're entitled to — in plain language.
          </p>
        </div>

        {/* Deadline card */}
        {denial && (
          <div className="mb-5 animate-fade-in-up stagger-1" style={{ ...card, borderLeft: "3px solid var(--gold)", borderRadius: "0 16px 16px 0", paddingLeft: "1.5rem", padding: "1.75rem 2rem" }}>
            <div className="flex items-start gap-4">
              <Clock size={19} style={{ color: "var(--gold)", flexShrink: 0, marginTop: "0.1rem" }} />
              <div className="flex-1">
                <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 600, color: "var(--text-primary)", marginBottom: "1.25rem" }}>
                  Your appeal deadlines
                </p>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
                      Internal appeal deadline
                    </span>
                    <div className="text-right">
                      <span style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-inter)" }}>
                        {formatDate(denial.deadline)}
                      </span>
                      {days !== null && (
                        <span className="ml-2" style={{ fontSize: "0.8rem", color: days < 60 ? "#92660A" : "var(--success)", fontFamily: "var(--font-inter)", fontWeight: 500 }}>
                          {days} days
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
                      External review available
                    </span>
                    <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
                      After internal decision
                    </span>
                  </div>
                </div>

                {/* Timeline */}
                <div className="mt-5 flex items-center gap-2 flex-wrap">
                  {["Now", "Internal Appeal", "Insurer Decision", "External Review", "Resolution"].map((step, i, arr) => (
                    <div key={step} className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full"
                        style={{ background: i === 0 ? "var(--gold)" : "rgba(15,31,61,0.15)" }} />
                      <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-inter)", color: i === 0 ? "var(--gold)" : "var(--text-tertiary)", fontWeight: i === 0 ? 600 : 400 }}>
                        {step}
                      </span>
                      {i < arr.length - 1 && (
                        <div style={{ width: "1.25rem", height: "1px", background: "rgba(15,31,61,0.12)" }} />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Your rights */}
        <div style={card} className="p-8 mb-5 animate-fade-in-up stagger-2">
          <div className="flex items-center gap-2.5 mb-6">
            <Shield size={17} style={{ color: "var(--gold)" }} />
            <h3 style={{ color: "var(--text-primary)" }}>Your rights</h3>
          </div>
          <ul className="space-y-5">
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
              <li key={i} className="flex items-start gap-3" style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.7 }}>
                <CheckCircle size={16} style={{ color: "var(--success)", flexShrink: 0, marginTop: "0.2rem" }} />
                {right}
              </li>
            ))}
          </ul>
        </div>

        {/* IRO card */}
        {reg && (
          <div style={card} className="p-8 mb-8 animate-fade-in-up stagger-3">
            <h3 style={{ color: "var(--text-primary)", marginBottom: "0.375rem" }}>Your independent reviewer</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginBottom: "1.25rem" }}>
              If your internal appeal fails, this is who reviews it next — independent of your insurer.
            </p>
            <div className="space-y-2">
              <p style={{ fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-inter)" }}>
                {reg.iro_name}
              </p>
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
                {reg.iro_phone}
              </p>
              {reg.iro_website !== "#" && (
                <a href={reg.iro_website} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 hover:underline transition-colors"
                  style={{ fontSize: "0.875rem", color: "var(--gold)", fontFamily: "var(--font-inter)" }}>
                  {reg.iro_website}
                  <ExternalLink size={12} />
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
