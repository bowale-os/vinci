"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Download, Copy, Play, Pause, CheckCircle, ArrowRight, Volume2 } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Nav } from "@/components/layout/Nav";
import { SkeletonCard } from "@/components/ui/Skeleton";
import api from "@/lib/api";
import type { AppealLetter } from "@/types";

const SECTIONS = [
  { key: "patient",   label: "Your information" },
  { key: "reference", label: "Why we're appealing" },
  { key: "evidence",  label: "Medical evidence" },
  { key: "rights",    label: "Your legal rights" },
  { key: "request",   label: "What we're asking for" },
];

function splitLetter(text: string): Record<string, string> {
  const lines = text.split("\n");
  const result: Record<string, string> = {};
  let current = "patient";
  for (const line of lines) {
    const l = line.toLowerCase();
    if (l.includes("re:") || l.includes("appeal") || l.includes("denial")) { current = "reference"; }
    else if (l.includes("evidence") || l.includes("study") || l.includes("pubmed") || l.includes("pmid")) { current = "evidence"; }
    else if (l.includes("law") || l.includes("statute") || l.includes("right") || l.includes("29 cfr") || l.includes("45 cfr")) { current = "rights"; }
    else if (l.includes("respectfully request") || l.includes("we request") || l.includes("therefore request")) { current = "request"; }
    result[current] = (result[current] ?? "") + line + "\n";
  }
  return result;
}

const card = {
  background: "#FFFFFF",
  border: "1px solid rgba(15,31,61,0.06)",
  borderRadius: "16px",
  boxShadow: "0 2px 8px rgba(15,31,61,0.06)",
};

export default function LetterPage() {
  const router = useRouter();
  const toast = useToast();
  const { denial, cptCode, clinicalNotes, patientState, appeal, setAppeal } = useVinci();
  const [loading, setLoading] = useState(false);
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [copied, setCopied] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (appeal) return;
    if (!denial) { router.push("/denial"); return; }
    setLoading(true);
    api.post<AppealLetter>("/api/appeal/generate", {
      denial,
      cpt_code: cptCode || "99214",
      clinical_notes: clinicalNotes || "Patient has documented medical history supporting this treatment.",
      patient_state: patientState,
    }).then(r => { setAppeal(r.data); toast("Your appeal letter is ready", "success"); })
      .catch(() => toast("This is taking longer than usual. We're still working on it.", "warning"))
      .finally(() => setLoading(false));
  }, [denial]);

  const letter = appeal;
  const sections = letter ? splitLetter(letter.letter_text) : {};

  const handleAudio = async () => {
    if (audioSrc) { audioRef.current?.play(); setPlaying(true); return; }
    if (!letter) return;
    setAudioLoading(true);
    try {
      const { data } = await api.post<{ audio_url: string }>("/api/appeal/audio", { letter_text: letter.letter_text });
      setAudioSrc(data.audio_url);
      setTimeout(() => { audioRef.current?.play(); setPlaying(true); }, 100);
    } catch { toast("This is taking longer than usual. We're still working on it.", "warning"); }
    finally { setAudioLoading(false); }
  };

  const handleCopy = () => {
    if (!letter) return;
    navigator.clipboard.writeText(letter.letter_text);
    setCopied(true);
    toast("Your appeal letter is ready — copied to clipboard", "success");
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownload = () => {
    if (!letter) return;
    const blob = new Blob([letter.letter_text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "vinci-appeal-letter.txt"; a.click();
    URL.revokeObjectURL(url);
    toast("Your appeal letter is ready — downloading PDF", "success");
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--warm-white)" }}>
      <Nav />
      <div className="pt-24 pb-20 px-6 max-w-3xl mx-auto">

        <div className="mb-8 animate-fade-in-up">
          <h1 style={{ color: "var(--text-primary)", marginBottom: "0.75rem" }}>Your appeal letter is ready</h1>
          <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)", maxWidth: "55ch" }}>
            Built on your insurer's own rules. Backed by medical evidence. Addressed to the right place.
          </p>
        </div>

        {loading && (
          <div className="space-y-4">
            <SkeletonCard /><SkeletonCard /><SkeletonCard />
          </div>
        )}

        {letter && !loading && (
          <>
            {/* Letter preview — paper feel */}
            <div className="paper-card rounded-[16px] overflow-hidden mb-5 animate-fade-in-up stagger-1">
              {SECTIONS.map(({ key, label }) => {
                const content = sections[key];
                if (!content?.trim()) return null;
                return (
                  <div key={key} style={{ borderBottom: "1px solid rgba(15,31,61,0.07)" }} className="last:border-0">
                    <div className="px-8 py-2.5" style={{ background: "rgba(15,31,61,0.025)", borderBottom: "1px solid rgba(15,31,61,0.06)" }}>
                      <span style={{ fontSize: "0.7rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                        {label}
                      </span>
                    </div>
                    <div className="px-8 py-6">
                      <p style={{ color: "#1A2A40", fontSize: "0.9rem", lineHeight: 1.85, whiteSpace: "pre-wrap", fontFamily: "Georgia, 'Times New Roman', serif" }}>
                        {content.trim()}
                      </p>
                    </div>
                  </div>
                );
              })}
              {Object.keys(sections).length === 0 && (
                <div className="px-8 py-8">
                  <p style={{ color: "#1A2A40", fontSize: "0.9rem", lineHeight: 1.85, whiteSpace: "pre-wrap", fontFamily: "Georgia, 'Times New Roman', serif" }}>
                    {letter.letter_text}
                  </p>
                </div>
              )}
            </div>

            {/* Audio player */}
            <div className="p-6 mb-5 rounded-[16px] animate-fade-in-up stagger-2"
              style={{ background: "var(--navy)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <Volume2 size={15} style={{ color: "var(--gold)" }} />
                  <p style={{ fontSize: "0.875rem", fontWeight: 500, color: "rgba(255,255,255,0.9)", fontFamily: "var(--font-inter)" }}>
                    Listen before you send
                  </p>
                </div>
                <span style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.35)", fontFamily: "var(--font-inter)" }}>
                  Catch anything before you submit.
                </span>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={playing ? () => { audioRef.current?.pause(); setPlaying(false); } : handleAudio}
                  disabled={audioLoading}
                  className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-transform duration-150 hover:scale-[1.06] disabled:opacity-40"
                  style={{ background: "var(--gold)" }}
                >
                  {audioLoading
                    ? <span className="w-4 h-4 border-2 border-[#0F1F3D] border-t-transparent rounded-full animate-spin" />
                    : playing
                      ? <Pause size={15} fill="#0F1F3D" color="#0F1F3D" />
                      : <Play  size={15} fill="#0F1F3D" color="#0F1F3D" style={{ marginLeft: "1px" }} />
                  }
                </button>
                {/* Waveform */}
                <div className="flex-1 flex items-center gap-0.5 h-8">
                  {Array.from({ length: 48 }).map((_, i) => (
                    <div key={i} className="flex-1 rounded-full transition-colors duration-300"
                      style={{
                        height: `${20 + Math.sin(i * 0.7) * 12 + ((i * 17) % 8)}px`,
                        background: playing ? "var(--gold)" : "rgba(255,255,255,0.15)",
                      }} />
                  ))}
                </div>
                {audioSrc && <audio ref={audioRef} src={audioSrc} onEnded={() => setPlaying(false)} className="hidden" />}
              </div>
            </div>

            {/* Citations */}
            {letter.citations?.length > 0 && (
              <div style={card} className="p-6 mb-5 animate-fade-in-up stagger-3">
                <p style={{ fontSize: "0.7rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "1rem" }}>
                  Medical evidence cited
                </p>
                <ul className="space-y-3">
                  {letter.citations.slice(0, 5).map(c => (
                    <li key={c.pmid ?? c.title} className="flex items-start gap-3" style={{ fontSize: "0.875rem" }}>
                      <span className="font-mono-ref shrink-0" style={{ color: "var(--gold)" }}>PMID:{c.pmid}</span>
                      <a href={c.url} target="_blank" rel="noopener noreferrer"
                        style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.5 }}
                        className="hover:underline hover:text-[#0F1F3D] transition-colors">
                        {c.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col gap-3 mb-6 animate-fade-in-up stagger-4">
              <Button size="lg" fullWidth onClick={handleDownload}>
                <Download size={18} /> Download as PDF
              </Button>
              <Button size="lg" variant="secondary" fullWidth onClick={handleCopy}>
                {copied ? <><CheckCircle size={18} /> Copied!</> : <><Copy size={18} /> Copy to clipboard</>}
              </Button>
            </div>

            {/* Submission instructions */}
            <div style={card} className="p-8 mb-5 animate-fade-in-up stagger-5">
              <h3 style={{ color: "var(--text-primary)", marginBottom: "1.25rem" }}>How to submit your appeal</h3>
              <ol className="space-y-4">
                {[
                  "Download or copy the letter above",
                  `Send to: ${denial?.insurer_name ?? "your insurer"}'s Appeals Department (address on your denial letter)`,
                  "Keep a copy for your records and note the date you submitted",
                  "If you don't hear back within 60 days, contact your state insurance department — that delay may itself be grounds for further action",
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-3" style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
                    <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                      style={{ background: "var(--gold-light)", color: "var(--gold)", fontFamily: "var(--font-mono)" }}>
                      {i + 1}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            {/* What happens next */}
            <div style={card} className="p-8 animate-fade-in-up">
              <h3 style={{ color: "var(--text-primary)", marginBottom: "1.25rem" }}>What happens next</h3>
              <div className="flex items-center gap-2 flex-wrap mb-4">
                {["You submit", "60 days for insurer", "If denied: external review", "82% of external reviews succeed"].map((s, i, arr) => (
                  <span key={s} className="flex items-center gap-2">
                    <span style={{ fontSize: "0.85rem", color: i === 0 ? "var(--text-primary)" : "var(--text-secondary)", fontFamily: "var(--font-inter)", fontWeight: i === 0 ? 500 : 400 }}>
                      {s}
                    </span>
                    {i < arr.length - 1 && <span style={{ color: "rgba(15,31,61,0.20)", fontSize: "0.75rem" }}>→</span>}
                  </span>
                ))}
              </div>
              <p style={{ fontSize: "0.875rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)" }}>
                Vinci saves your appeal so you can track its status and escalate if needed.
              </p>
            </div>
          </>
        )}

        {!loading && !letter && (
          <div className="text-center py-20 animate-fade-in-up">
            <p style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginBottom: "1.5rem" }}>
              Upload your denial letter above and we'll get started
            </p>
            <Button variant="secondary" onClick={() => router.push("/denial")}>Upload denial letter</Button>
          </div>
        )}
      </div>
    </div>
  );
}
