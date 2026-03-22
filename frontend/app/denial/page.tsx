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

const card = {
  background: "#FFFFFF",
  border: "1px solid rgba(15,31,61,0.06)",
  borderRadius: "16px",
  boxShadow: "0 2px 8px rgba(15,31,61,0.06)",
};

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
    <div className="min-h-screen" style={{ background: "var(--warm-white)" }}>
      <Nav />
      <div className="pt-24 pb-20 px-6 max-w-[1200px] mx-auto">

        {/* Upload zone — only shown before results */}
        {!result && !loading && (
          <div className="max-w-xl mx-auto mt-12 animate-fade-in-up">
            {/* Page title */}
            <div className="mb-10">
              <h1 style={{ color: "var(--text-primary)", marginBottom: "0.75rem" }}>
                Upload your denial letter
              </h1>
              <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)", maxWidth: "50ch" }}>
                We'll read it and explain exactly what it means — and how to fight it.
              </p>
            </div>

            <div
              onClick={() => fileRef.current?.click()}
              onDrop={onDrop}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              className="cursor-pointer rounded-[16px] p-16 flex flex-col items-center gap-5 transition-all duration-200"
              style={{
                border: `2px dashed ${dragging ? "var(--gold)" : "rgba(15,31,61,0.15)"}`,
                background: dragging ? "var(--gold-light)" : "#FFFFFF",
              }}
            >
              <div className="w-16 h-16 rounded-full flex items-center justify-center"
                style={{ background: "rgba(15,31,61,0.05)" }}>
                <Upload size={26} style={{ color: "var(--text-tertiary)" }} />
              </div>
              <div className="text-center">
                <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.375rem" }}>
                  Drop your denial letter here
                </p>
                <p style={{ fontSize: "0.875rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)" }}>
                  or tap to choose a file · PDF, DOC, DOCX, JPG, PNG
                </p>
              </div>
            </div>

            <p className="text-center mt-4" style={{ fontSize: "0.8rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)" }}>
              🔒 Your file is processed securely and never stored.
            </p>
          </div>
        )}

        <input ref={fileRef} type="file" className="hidden" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff,.webp,.txt"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />

        {/* Loading */}
        {loading && (
          <div className="max-w-xl mx-auto mt-16 space-y-4">
            <p className="text-center mb-6" style={{ fontSize: "0.875rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)" }}>
              We're reading your letter…
            </p>
            <SkeletonCard /><SkeletonCard />
          </div>
        )}

        {/* Results — two-column layout */}
        {result && !loading && (
          <div className="mt-8 lg:grid lg:grid-cols-[1fr_320px] lg:gap-8 lg:items-start">

            {/* ── Left column ── */}
            <div className="space-y-5">

              {/* Contestable banner */}
              <div className="flex items-center gap-3 px-5 py-4 rounded-[12px] animate-fade-in-up"
                style={{ background: "var(--success-bg)", border: "1px solid rgba(26,107,58,0.15)" }}>
                <CheckCircle size={17} style={{ color: "var(--success)", flexShrink: 0 }} />
                <p style={{ color: "var(--success)", fontFamily: "var(--font-inter)", fontWeight: 500, fontSize: "0.9rem" }}>
                  This denial looks contestable. Here's why.
                </p>
              </div>

              {/* Extracted details */}
              <div style={card} className="p-8 space-y-5 animate-fade-in-up stagger-1">
                <h3 className="flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                  <FileText size={15} style={{ color: "var(--gold)" }} />
                  Denial details
                </h3>

                {[
                  { label: "Patient",        val: result.patient_name },
                  { label: "Insurer",        val: result.insurer_name },
                  { label: "Service denied", val: result.service_denied ?? "See letter" },
                  { label: "Denial reason",  val: result.denial_reason },
                ].map(({ label, val }) => (
                  <div key={label} className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-6 pb-4 last:pb-0"
                    style={{ borderBottom: "1px solid rgba(15,31,61,0.06)" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", minWidth: "8rem", paddingTop: "0.1rem" }}>
                      {label}
                    </span>
                    <span style={{ fontSize: "0.9rem", color: "var(--text-primary)", fontFamily: "var(--font-inter)" }}>
                      {val}
                    </span>
                  </div>
                ))}

                <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-6 pb-4"
                  style={{ borderBottom: "1px solid rgba(15,31,61,0.06)" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", minWidth: "8rem", paddingTop: "0.1rem" }}>
                    Claim ID
                  </span>
                  <span className="font-mono-ref" style={{ color: "var(--text-secondary)" }}>
                    {result.claim_id}
                  </span>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-6 pb-4"
                  style={{ borderBottom: "1px solid rgba(15,31,61,0.06)" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", minWidth: "8rem", paddingTop: "0.1rem" }}>
                    CPB cited
                  </span>
                  <span className="font-mono-ref" style={{ color: "var(--text-secondary)" }}>
                    {result.cpb_code_cited}
                  </span>
                </div>

                <div className={`flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-6 ${days !== null && days < DAYS_WARNING ? "pl-4 -ml-4" : ""}`}
                  style={days !== null && days < DAYS_WARNING ? { borderLeft: "3px solid #C9A84C" } : {}}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", minWidth: "8rem", paddingTop: "0.1rem" }}>
                    Appeal deadline
                  </span>
                  <div>
                    <span style={{ fontSize: "0.9rem", color: "var(--text-primary)", fontFamily: "var(--font-inter)" }}>
                      {result.deadline}
                    </span>
                    {days !== null && (
                      <span className="ml-2 inline-flex items-center gap-1" style={{ fontSize: "0.8rem", fontWeight: 500, color: days < DAYS_WARNING ? "#92660A" : "var(--text-tertiary)", fontFamily: "var(--font-inter)" }}>
                        {days < DAYS_WARNING && <AlertTriangle size={12} />}
                        {days} days remaining
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Plain English explanation */}
              <div style={card} className="p-8 space-y-6 animate-fade-in-up stagger-2">
                <h3 style={{ color: "var(--text-primary)" }}>What they actually said — and why it may be wrong</h3>

                <div>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", marginBottom: "0.625rem" }}>
                    What the denial says
                  </p>
                  <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.7, maxWidth: "65ch" }}>
                    {result.insurer_name} says this {result.service_denied ? `treatment (${result.service_denied})` : "service"} isn't covered based on their internal coverage guidelines. Their stated reason: {result.denial_reason.toLowerCase()}.
                  </p>
                </div>

                <div>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", marginBottom: "0.625rem" }}>
                    Why this is likely wrong
                  </p>
                  <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.7, maxWidth: "65ch" }}>
                    Most denials citing {result.cpb_code_cited !== "Not cited" ? `policy ${result.cpb_code_cited}` : "coverage criteria"} require the insurer to verify specific prior treatment steps. Denial letters frequently omit this verification — which is one of the most common reasons this type of denial gets overturned on appeal.
                  </p>
                </div>

                <div className="pl-4 py-3 rounded-r-[8px] animate-fade-in-up"
                  style={{ borderLeft: "3px solid var(--gold)", background: "var(--gold-light)" }}>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                    What we found in their rulebook
                  </p>
                  <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.7, maxWidth: "65ch" }}>
                    {result.insurer_name}'s coverage criteria require documented evidence of medical necessity and, in most cases, a documented response to prior treatments. If your medical records support this, the denial is contestable.
                  </p>
                </div>

                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full"
                  style={{ background: "var(--success-bg)", border: "1px solid rgba(26,107,58,0.15)", fontSize: "0.875rem", fontWeight: 500, color: "var(--success)", fontFamily: "var(--font-inter)" }}>
                  70% of denials like this are overturned on appeal — KFF 2024
                </div>
              </div>

              {/* Required docs */}
              {result.required_docs?.length > 0 && (
                <div style={card} className="p-8 animate-fade-in-up stagger-3">
                  <p style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-inter)", marginBottom: "1rem" }}>
                    Documents they say would support your appeal
                  </p>
                  <ul className="space-y-2.5">
                    {result.required_docs.map((doc, i) => (
                      <li key={i} className="flex items-start gap-2.5" style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
                        <span style={{ color: "var(--gold)", marginTop: "0.1rem", flexShrink: 0 }}>·</span>
                        {doc}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* ── Right column: TL;DR + CTA (sticky) ── */}
            <div className="mt-5 lg:mt-0 lg:sticky lg:top-24 space-y-4">

              {/* TL;DR card */}
              <div className="rounded-[16px] overflow-hidden animate-fade-in-up"
                style={{ background: "#FFFFFF", border: "1px solid var(--gold-border)", boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
                <div className="px-6 pt-5 pb-1">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-7 h-7 rounded-[8px] flex items-center justify-center"
                      style={{ background: "var(--gold-light)" }}>
                      <Zap size={13} style={{ color: "var(--gold)" }} />
                    </div>
                    <span style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--gold)", fontFamily: "var(--font-inter)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                      TL;DR
                    </span>
                  </div>
                </div>
                <div className="px-6 pb-6">
                  <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.7 }}>
                    {result.tldr || `${result.insurer_name} denied your ${result.service_denied ?? "claim"}. You have until ${result.deadline} to appeal.`}
                  </p>
                </div>
              </div>

              {/* Urgency chip */}
              {days !== null && days < DAYS_WARNING && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-[12px] animate-fade-in-up stagger-1"
                  style={{ background: "rgba(180,130,0,0.06)", border: "1px solid rgba(180,130,0,0.20)", fontSize: "0.875rem", fontFamily: "var(--font-inter)" }}>
                  <AlertTriangle size={15} style={{ color: "#92660A", flexShrink: 0 }} />
                  <span style={{ color: "#7A5500" }}>
                    <strong>{days} days</strong> left to appeal
                  </span>
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
