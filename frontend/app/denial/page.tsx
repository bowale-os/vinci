"use client";
import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, CheckCircle, ArrowRight, AlertTriangle, Zap } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Nav } from "@/components/layout/Nav";
import { SkeletonCard } from "@/components/ui/Skeleton";
import type { DenialParseResult } from "@/types";

const DAYS_WARNING = 60;

function daysUntil(dateStr: string): number | null {
  if (!dateStr || dateStr === "Not specified") return null;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  return Math.ceil((d.getTime() - Date.now()) / 86400000);
}

export default function DenialPage() {
  const router = useRouter();
  const toast = useToast();
  const { setDenial } = useVinci();
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DenialParseResult | null>(null);

  const handleFile = useCallback(async (file: File) => {
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${baseUrl}/api/denial/parse`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        console.error("Parse error:", res.status, detail);
        if (detail?.includes("Unsupported")) toast("We had trouble reading that file. Try a clearer photo or a different format.", "warning");
        else toast(`Upload failed (${res.status}): ${detail || "unknown error"}`, "warning");
        return;
      }
      const data: DenialParseResult = await res.json();
      setResult(data);
      setDenial(data);
      toast("We found your denial details. Review below.", "success");
    } catch (err: any) {
      console.error("Upload error:", err);
      toast("Could not reach the server. Is the backend running?", "warning");
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }, [setDenial, toast]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const days = result ? daysUntil(result.deadline) : null;

  return (
    <div className="min-h-screen bg-slate-950">
      <Nav />
      <div className="pt-20 pb-16 px-4 max-w-6xl mx-auto">

        {/* Drop zone — only shown before results */}
        {!result && !loading && (
          <div className="max-w-xl mx-auto mt-16">
            <div
              onClick={() => fileRef.current?.click()}
              onDrop={onDrop}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              className={`cursor-pointer border-2 border-dashed rounded-2xl p-16 flex flex-col items-center gap-4 transition-all ${dragging ? "border-[#C9A84C] bg-[#C9A84C]/5" : "border-slate-700 hover:border-slate-500 bg-slate-900/40"}`}
            >
              <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center">
                <Upload size={28} className="text-slate-400" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-slate-200 mb-1">Drop your denial letter here</p>
                <p className="text-sm text-slate-500">or tap to choose a file · PDF, DOC, DOCX, JPG, PNG</p>
              </div>
            </div>
          </div>
        )}

        <input ref={fileRef} type="file" className="hidden" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff,.webp,.txt"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />

        {/* Loading */}
        {loading && (
          <div className="max-w-xl mx-auto mt-16 space-y-4">
            <p className="text-sm text-slate-500 text-center mb-4">We're reading your letter…</p>
            <SkeletonCard /><SkeletonCard />
          </div>
        )}

        {/* Results — two-column layout */}
        {result && !loading && (
          <div className="mt-8 lg:grid lg:grid-cols-[1fr_320px] lg:gap-8 lg:items-start">

            {/* ── Left column: details ── */}
            <div className="space-y-5">
              {/* Contestable banner */}
              <div className="flex items-center gap-3 px-5 py-3.5 rounded-xl bg-emerald-500/8 border border-emerald-500/20">
                <CheckCircle size={18} className="text-emerald-400 shrink-0" />
                <p className="text-emerald-300 font-medium">This denial looks contestable. Here's why.</p>
              </div>

              {/* Extracted details */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <h2 className="font-semibold text-slate-100 flex items-center gap-2">
                  <FileText size={16} className="text-[#C9A84C]" /> Denial details
                </h2>
                {[
                  { label: "Patient",        val: result.patient_name },
                  { label: "Insurer",        val: result.insurer_name },
                  { label: "Service denied", val: result.service_denied ?? "See letter" },
                  { label: "Denial reason",  val: result.denial_reason },
                ].map(({ label, val }) => (
                  <div key={label} className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 border-b border-slate-800/60 pb-3 last:border-0 last:pb-0">
                    <span className="text-xs text-slate-500 uppercase tracking-wide w-32 shrink-0 pt-0.5">{label}</span>
                    <span className="text-slate-200 text-sm">{val}</span>
                  </div>
                ))}
                <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 border-b border-slate-800/60 pb-3">
                  <span className="text-xs text-slate-500 uppercase tracking-wide w-32 shrink-0 pt-0.5">Claim ID</span>
                  <span className="font-mono text-slate-300 text-sm">{result.claim_id}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 border-b border-slate-800/60 pb-3">
                  <span className="text-xs text-slate-500 uppercase tracking-wide w-32 shrink-0 pt-0.5">CPB cited</span>
                  <span className="font-mono text-slate-300 text-sm">{result.cpb_code_cited}</span>
                </div>
                <div className={`flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 pl-3 -ml-3 ${days !== null && days < DAYS_WARNING ? "border-l-2 border-amber-400" : ""}`}>
                  <span className="text-xs text-slate-500 uppercase tracking-wide w-32 shrink-0 pt-0.5">Appeal deadline</span>
                  <div>
                    <span className="text-slate-200 text-sm">{result.deadline}</span>
                    {days !== null && (
                      <span className={`ml-2 text-xs font-medium ${days < DAYS_WARNING ? "text-amber-400" : "text-slate-500"}`}>
                        {days < DAYS_WARNING && <AlertTriangle size={12} className="inline mr-1" />}
                        {days} days remaining
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Plain English explanation */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                <h2 className="font-semibold text-slate-100">What they actually said — and why it may be wrong</h2>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">What the denial says</p>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    {result.insurer_name} says this {result.service_denied ? `treatment (${result.service_denied})` : "service"} isn't covered based on their internal coverage guidelines. Their stated reason: {result.denial_reason.toLowerCase()}.
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Why this is likely wrong</p>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    Most denials citing {result.cpb_code_cited !== "Not cited" ? `policy ${result.cpb_code_cited}` : "coverage criteria"} require the insurer to verify specific prior treatment steps. Denial letters frequently omit this verification — which is one of the most common reasons this type of denial gets overturned on appeal.
                  </p>
                </div>
                <div className="border-l-2 border-[#C9A84C] pl-4 py-2 bg-[#C9A84C]/5 rounded-r-xl">
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">What we found in their rulebook</p>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    {result.insurer_name}'s coverage criteria require documented evidence of medical necessity and, in most cases, a documented response to prior treatments. If your medical records support this, the denial is contestable.
                  </p>
                </div>
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
                  style={{ background: "rgba(26,107,58,0.08)", color: "#22c55e", border: "1px solid rgba(34,197,94,0.15)" }}>
                  70% of denials like this are overturned on appeal — KFF 2024
                </div>
              </div>

              {/* Required docs */}
              {result.required_docs?.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <p className="text-sm font-medium text-slate-300 mb-3">Documents they say would support your appeal</p>
                  <ul className="space-y-2">
                    {result.required_docs.map((doc, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                        <span className="text-[#C9A84C] mt-0.5">·</span> {doc}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* ── Right column: TL;DR + CTA (sticky on desktop) ── */}
            <div className="mt-5 lg:mt-0 lg:sticky lg:top-24 space-y-4">
              {/* TL;DR card */}
              <div className="relative rounded-2xl overflow-hidden border border-[#C9A84C]/30 bg-slate-900">
                {/* Glow accent */}
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#C9A84C]/60 to-transparent" />
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-7 h-7 rounded-lg bg-[#C9A84C]/15 flex items-center justify-center">
                      <Zap size={14} className="text-[#C9A84C]" />
                    </div>
                    <span className="text-xs font-semibold text-[#C9A84C] uppercase tracking-widest">TL;DR</span>
                  </div>
                  <p className="text-slate-200 text-sm leading-relaxed">
                    {result.tldr || `${result.insurer_name} denied your ${result.service_denied ?? "claim"}. You have until ${result.deadline} to appeal.`}
                  </p>
                </div>
              </div>

              {/* Urgency chip */}
              {days !== null && days < DAYS_WARNING && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-500/8 border border-amber-500/20 text-amber-300 text-sm">
                  <AlertTriangle size={15} className="shrink-0" />
                  <span><strong>{days} days</strong> left to appeal</span>
                </div>
              )}

              {/* CTA */}
              <Button size="lg" fullWidth onClick={() => router.push("/appeal/financial")}>
                See the financial impact <ArrowRight size={18} />
              </Button>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
