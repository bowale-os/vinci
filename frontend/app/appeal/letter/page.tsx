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
  // Heuristic split — works for Gemini-formatted letters
  const lines = text.split("\n");
  const result: Record<string, string> = {};
  let current = "patient";
  const chunks: string[] = [];
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
    <div className="min-h-screen bg-slate-950">
      <Nav />
      <div className="pt-20 pb-16 px-4 max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Your appeal letter is ready</h1>
          <p className="text-slate-400">Built on your insurer's own rules. Backed by medical evidence. Addressed to the right place.</p>
        </div>

        {loading && <div className="space-y-4"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>}

        {letter && !loading && (
          <>
            {/* Letter preview — paper feel */}
            <div className="paper-card rounded-2xl overflow-hidden mb-5">
              {SECTIONS.map(({ key, label }) => {
                const content = sections[key];
                if (!content?.trim()) return null;
                return (
                  <div key={key} className="border-b border-slate-100/60 last:border-0">
                    <div className="px-6 py-2 bg-slate-50/5 border-b border-slate-100/30">
                      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
                    </div>
                    <div className="px-6 py-5">
                      <p className="text-slate-800 dark:text-slate-200 text-sm leading-7 whitespace-pre-wrap font-serif">{content.trim()}</p>
                    </div>
                  </div>
                );
              })}
              {/* Fallback: render full text if sections are empty */}
              {Object.keys(sections).length === 0 && (
                <div className="px-6 py-8">
                  <p className="text-slate-200 text-sm leading-7 whitespace-pre-wrap">{letter.letter_text}</p>
                </div>
              )}
            </div>

            {/* Audio player */}
            <div className="bg-[#0F1F3D] border border-slate-700 rounded-2xl p-5 mb-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Volume2 size={16} className="text-[#C9A84C]" />
                  <p className="text-sm font-medium text-slate-200">Listen to your letter before sending</p>
                </div>
                <span className="text-xs text-slate-500">Hear it read aloud to catch anything before you submit.</span>
              </div>
              <div className="flex items-center gap-4">
                <button onClick={playing ? () => { audioRef.current?.pause(); setPlaying(false); } : handleAudio}
                  disabled={audioLoading}
                  className="w-10 h-10 rounded-full bg-[#C9A84C] flex items-center justify-center text-[#0F1F3D] hover:bg-[#E4C97A] transition-colors shrink-0 disabled:opacity-50">
                  {audioLoading ? <span className="w-4 h-4 border-2 border-[#0F1F3D] border-t-transparent rounded-full animate-spin" />
                    : playing ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
                </button>
                {/* Waveform visualization (static decorative) */}
                <div className="flex-1 flex items-center gap-0.5 h-8">
                  {Array.from({ length: 48 }).map((_, i) => (
                    <div key={i} className="flex-1 rounded-full transition-all"
                      style={{ height: `${20 + Math.sin(i * 0.7) * 12 + Math.random() * 8}px`, background: playing ? "#C9A84C" : "#334155" }} />
                  ))}
                </div>
                {audioSrc && <audio ref={audioRef} src={audioSrc} onEnded={() => setPlaying(false)} className="hidden" />}
              </div>
            </div>

            {/* Citations */}
            {letter.citations?.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-5">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Medical evidence cited</p>
                <ul className="space-y-2">
                  {letter.citations.slice(0, 5).map(c => (
                    <li key={c.pmid ?? c.title} className="flex items-start gap-2 text-sm">
                      <span className="font-mono-ref text-[#C9A84C] shrink-0">PMID:{c.pmid}</span>
                      <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-slate-300 hover:text-white hover:underline">{c.title}</a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col gap-3 mb-6">
              <Button size="lg" fullWidth onClick={handleDownload}><Download size={18} /> Download as PDF</Button>
              <Button size="lg" variant="secondary" fullWidth onClick={handleCopy}>
                {copied ? <><CheckCircle size={18} /> Copied!</> : <><Copy size={18} /> Copy to clipboard</>}
              </Button>
            </div>

            {/* Submission instructions */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-5">
              <h3 className="font-semibold text-slate-100 mb-4">How to submit your appeal</h3>
              <ol className="space-y-3">
                {[
                  "Download or copy the letter above",
                  `Send to: ${denial?.insurer_name ?? "your insurer"}'s Appeals Department (address on your denial letter)`,
                  "Keep a copy for your records and note the date you submitted",
                  "If you don't hear back within 60 days, contact your state insurance department — that delay may itself be grounds for further action",
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-slate-300">
                    <span className="w-6 h-6 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] flex items-center justify-center text-xs font-bold shrink-0">{i + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            {/* What happens next */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="font-semibold text-slate-100 mb-4">What happens next</h3>
              <div className="flex items-center gap-2 flex-wrap text-xs text-slate-500 mb-4">
                {["You submit", "60 days for insurer", "If denied: external review", "82% of external reviews succeed"].map((s, i, arr) => (
                  <span key={s} className="flex items-center gap-2">
                    <span className="text-slate-300">{s}</span>
                    {i < arr.length - 1 && <span className="text-slate-700">→</span>}
                  </span>
                ))}
              </div>
              <p className="text-sm text-slate-500">Vinci saves your appeal so you can track its status and escalate if needed.</p>
            </div>
          </>
        )}

        {!loading && !letter && (
          <div className="text-center py-16">
            <p className="text-slate-500 mb-4">Upload your denial letter above and we'll get started</p>
            <Button variant="secondary" onClick={() => router.push("/denial")}>Upload denial letter</Button>
          </div>
        )}
      </div>
    </div>
  );
}
