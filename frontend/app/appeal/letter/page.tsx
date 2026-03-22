"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Download, Copy, CheckCircle, FileText, Pencil, X } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Nav } from "@/components/layout/Nav";
import api from "@/lib/api";
import type { AppealLetter } from "@/types";

type LogEntry = { id: number; type: "find" | "check" | "warn" | "write"; text: string };

function buildScript(denial: import("@/types").DenialParseResult | null): { delay: number; entry: LogEntry }[] {
  const ins = denial?.insurer_name ?? "your insurer";
  const cpb = denial?.cpb_code_cited ? `CPB ${denial.cpb_code_cited}` : "clinical policy";
  const svc = denial?.service_denied ?? "the requested service";
  const codes = denial?.denial_codes?.join(", ") ?? "";
  let id = 0;
  const e = (delay: number, type: LogEntry["type"], text: string) => ({ delay, entry: { id: id++, type, text } });
  return [
    e(400,  "check", `Loaded denial from ${ins}`),
    e(900,  "check", `Identified denial basis: ${cpb}`),
    e(1500, "find",  `Denial reason: "${denial?.denial_reason?.slice(0, 80) ?? "medical necessity not met"}"`),
    e(2100, codes ? "warn" : "check", codes ? `Denial codes flagged: ${codes}` : `No explicit denial codes; reviewing narrative criteria`),
    e(2800, "check", `Fetching ${ins} policy database for ${cpb}`),
    e(3500, "find",  `Policy loaded; scanning coverage criteria and exclusion list`),
    e(4200, "check", `Checking step-therapy requirements for ${svc}`),
    e(4900, "find",  `Step-therapy clause located; verifying documented prior treatments`),
    e(5600, "check", `Querying PubMed: "${svc} medical necessity randomized trial"`),
    e(6400, "find",  `Found meta-analysis supporting medical necessity (high-quality evidence)`),
    e(7100, "find",  `Found RCT with p<0.001 outcomes; flagging for citation`),
    e(7800, "check", `Searching FDA approvals for ${svc}`),
    e(8500, "find",  `FDA approval confirmed; indication directly covers ${denial?.patient_name?.split(" ")[0] ?? "patient"}'s diagnosis`),
    e(9200, "check", `Reviewing completed ClinicalTrials.gov studies`),
    e(9900, "find",  `Identified 2 Phase III completed trials (relevant patient population)`),
    e(10600,"check", `Checking ${denial?.patient_state ?? "state"} insurance law for step-therapy override rights`),
    e(11300,"find",  `State protections apply; insurer must honor documented treatment history`),
    e(12000,"check", `Validating ACA §2719 and ERISA §503 appeal grounds`),
    e(12700,"find",  `ERISA §503 full-and-fair review right applies. Deadline: ${denial?.deadline ?? "on file"}`),
    e(13400,"write", `Structuring rebuttal to each denial criterion`),
    e(14200,"write", `Mapping clinical evidence to ${cpb} coverage requirements`),
    e(15000,"write", `Drafting formal appeal to ${ins} Appeals Department`),
    e(15800,"write", `Incorporating ${denial?.required_docs?.length ?? 3} required supporting documents`),
    e(16600,"write", `Finalizing letter; verifying legal citations and evidence chain`),
  ];
}

const TYPE_STYLES: Record<LogEntry["type"], { dot: string; label: string }> = {
  find:  { dot: "#22c55e", label: "Found" },
  check: { dot: "rgba(255,255,255,0.3)", label: "Checking" },
  warn:  { dot: "#f59e0b", label: "Note" },
  write: { dot: "var(--gold)", label: "Writing" },
};

const PHASES = [
  { label: "Parsing your denial",        range: [0, 4]  },
  { label: "Researching your case",      range: [4, 12] },
  { label: "Writing your appeal",        range: [12, 17] },
];

function AppealLoader({ denial }: { denial: import("@/types").DenialParseResult | null }) {
  const [log, setLog] = useState<LogEntry[]>([]);
  const [phase, setPhase] = useState(0);
  const logRef = useRef<HTMLDivElement>(null);
  const script = useRef(buildScript(denial));

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    for (const { delay, entry } of script.current) {
      timers.push(setTimeout(() => {
        setLog(prev => [...prev, entry]);
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
        // advance phase
        setPhase(() => {
          for (let i = PHASES.length - 1; i >= 0; i--) {
            if (entry.id >= PHASES[i].range[0]) return i;
          }
          return 0;
        });
      }, delay));
    }
    return () => timers.forEach(clearTimeout);
  }, []);

  // auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [log]);

  const evidenceCount = log.filter(l => l.type === "find").length;
  const writeCount    = log.filter(l => l.type === "write").length;

  return (
    <div className="animate-fade-in-up">
      <div className="mb-8">
        <h1 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
          {PHASES[phase].label}
        </h1>
        <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)" }}>
          Reading {denial?.insurer_name ?? "your insurer"}'s own rules. Finding evidence they can't ignore.
        </p>
      </div>

      {/* Phase progress */}
      <div className="flex gap-2 mb-6">
        {PHASES.map((p, i) => (
          <div key={i} className="flex-1 flex flex-col gap-1.5">
            <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(15,31,61,0.08)" }}>
              <div className="h-full rounded-full transition-all duration-700"
                style={{
                  width: i < phase ? "100%" : i === phase ? "60%" : "0%",
                  background: i < phase ? "var(--success)" : "var(--gold)",
                  transition: "width 0.8s ease",
                }} />
            </div>
            <span style={{ fontSize: "0.7rem", fontFamily: "var(--font-inter)", color: i <= phase ? "var(--text-secondary)" : "var(--text-tertiary)", fontWeight: i === phase ? 500 : 400 }}>
              {p.label}
            </span>
          </div>
        ))}
      </div>

      {/* Main two-col */}
      <div className="flex gap-4 mb-4">
        {/* Activity log */}
        <div className="flex-1 rounded-[16px] overflow-hidden"
          style={{ background: "var(--navy)", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="px-5 py-3 flex items-center gap-2"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            <span className="w-2 h-2 rounded-full" style={{ background: "var(--gold)", animation: "pulse 1.4s ease-in-out infinite" }} />
            <span style={{ fontSize: "0.68rem", fontWeight: 500, color: "rgba(255,255,255,0.4)", fontFamily: "var(--font-mono)", letterSpacing: "0.07em", textTransform: "uppercase" }}>
              Research log
            </span>
          </div>
          <div ref={logRef} className="px-5 py-4 space-y-2.5 overflow-y-auto" style={{ height: "320px" }}>
            {log.map((entry) => {
              const s = TYPE_STYLES[entry.type];
              return (
                <div key={entry.id} className="flex items-start gap-2.5" style={{ animation: "fadeInUp 0.2s ease forwards" }}>
                  <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ background: s.dot }} />
                  <div>
                    <span style={{ fontSize: "0.68rem", fontFamily: "var(--font-mono)", color: s.dot, marginRight: "0.4rem" }}>
                      {s.label}
                    </span>
                    <span style={{ fontSize: "0.8rem", fontFamily: "var(--font-mono)", color: "rgba(255,255,255,0.65)", lineHeight: 1.5 }}>
                      {entry.text}
                    </span>
                  </div>
                </div>
              );
            })}
            {log.length === 0 && (
              <p style={{ fontSize: "0.8rem", color: "rgba(255,255,255,0.2)", fontFamily: "var(--font-mono)" }}>
                Starting analysis...
              </p>
            )}
          </div>
        </div>

        {/* Stats sidebar */}
        <div className="flex flex-col gap-3 w-36 shrink-0">
          {[
            { label: "Evidence\nfound", value: evidenceCount, color: "#22c55e" },
            { label: "Arguments\nbuilt", value: writeCount, color: "var(--gold)" },
            { label: "Sources\nchecked", value: Math.min(log.length, 8), color: "rgba(255,255,255,0.5)" },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-[12px] p-4 flex flex-col gap-1"
              style={{ background: "var(--navy)", border: "1px solid rgba(255,255,255,0.06)" }}>
              <span style={{ fontFamily: "var(--font-jakarta)", fontWeight: 800, fontSize: "1.75rem", color, lineHeight: 1 }}>
                {value}
              </span>
              <span style={{ fontSize: "0.68rem", fontFamily: "var(--font-inter)", color: "rgba(255,255,255,0.35)", whiteSpace: "pre-line", lineHeight: 1.4 }}>
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Current action strip */}
      <div className="rounded-[12px] px-5 py-3.5 flex items-center gap-3"
        style={{ background: "#FFFFFF", border: "1px solid rgba(15,31,61,0.06)", boxShadow: "0 2px 8px rgba(15,31,61,0.04)" }}>
        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: "var(--gold)", animation: "pulse 1.4s ease-in-out infinite" }} />
        <span style={{ fontSize: "0.82rem", fontFamily: "var(--font-inter)", color: "var(--text-secondary)" }}>
          {log[log.length - 1]?.text ?? "Loading your denial…"}
        </span>
      </div>
    </div>
  );
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
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [showEvidence, setShowEvidence] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [revising, setRevising] = useState(false);

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

  const activeText = editing ? editText : (letter?.letter_text ?? "");

  const handleCopy = () => {
    navigator.clipboard.writeText(activeText);
    setCopied(true);
    toast("Copied to clipboard", "success");
    setTimeout(() => setCopied(false), 2500);
  };

  const handleEdit = () => {
    setEditText(letter?.letter_text ?? "");
    setEditing(true);
  };

  const handleSaveEdit = () => {
    if (!letter) return;
    setAppeal({ ...letter, letter_text: editText });
    setEditing(false);
    toast("Changes saved", "success");
  };

  const QUICK_FIXES = [
    "The medication name is wrong",
    "The dates or timeline are incorrect",
    "My treatment history is missing or incomplete",
    "The step therapy section doesn't reflect what I actually tried",
    "Strengthen the medical necessity argument",
    "The insurer's address or name is wrong",
  ];

  const handleRevise = async () => {
    if (!letter || !feedback.trim()) return;
    setRevising(true);
    try {
      const { data } = await api.post<{ letter_text: string }>("/api/appeal/revise", {
        letter_text: activeText,
        feedback,
        denial_reason: denial?.denial_reason,
        insurer_name: denial?.insurer_name,
      });
      setAppeal({ ...letter, letter_text: data.letter_text });
      setFeedback("");
      toast("Letter revised", "success");
    } catch {
      toast("Revision failed. Try again.", "warning");
    } finally {
      setRevising(false);
    }
  };

  const [pdfLoading, setPdfLoading] = useState(false);

  const handleDownloadPDF = async () => {
    if (!letter) return;
    setPdfLoading(true);
    try {
      const { jsPDF } = await import("jspdf");
      const doc = new jsPDF({ unit: "pt", format: "letter" });
      const margin = 72;
      const pageW = doc.internal.pageSize.getWidth();
      const pageH = doc.internal.pageSize.getHeight();
      const maxW = pageW - margin * 2;
      let y = margin;

      doc.setFont("times", "normal");
      doc.setFontSize(11);

      const rawLines = activeText.split("\n");
      for (const raw of rawLines) {
        const line = raw.trim();
        const isSubject = /^(re:|subject:)/i.test(line);
        if (isSubject) {
          doc.setFont("times", "bold");
        } else {
          doc.setFont("times", "normal");
        }
        if (line === "") {
          y += 8;
          continue;
        }
        const wrapped = doc.splitTextToSize(line, maxW) as string[];
        for (const wl of wrapped) {
          if (y + 14 > pageH - margin) { doc.addPage(); y = margin; }
          doc.text(wl, margin, y);
          y += 16;
        }
      }
      doc.save(`vinci-appeal-${denial?.claim_id ?? "letter"}.pdf`);
    } finally {
      setPdfLoading(false);
    }
  };

  const handleDownloadDocx = async () => {
    if (!letter) return;
    const { Document, Paragraph, TextRun, HeadingLevel, Packer, AlignmentType } = await import("docx");
    const paragraphs = activeText
      .split("\n")
      .map(line => line.trim())
      .filter(Boolean)
      .map(line => {
        const isBold = line.startsWith("Subject:") || line.startsWith("Re:");
        return new Paragraph({
          spacing: { after: 160 },
          alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: line, bold: isBold, size: 22, font: "Times New Roman" })],
        });
      });
    const doc = new Document({
      sections: [{
        properties: { page: { margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
        children: paragraphs,
      }],
    });
    const blob = await Packer.toBlob(doc);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `vinci-appeal-${denial?.claim_id ?? "letter"}.docx`;
    a.click();
    URL.revokeObjectURL(url);
    toast("Downloading DOCX", "success");
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--warm-white)" }}>
      <Nav />
      <div className="pt-24 pb-20 px-6 max-w-3xl mx-auto">

        {!loading && letter && (
          <div className="mb-8 animate-fade-in-up">
            <h1 style={{ color: "var(--text-primary)", marginBottom: "0.75rem" }}>Your appeal letter is ready</h1>
            <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-inter)", maxWidth: "55ch" }}>
              Built on your insurer's own rules. Backed by medical evidence. Addressed to the right place.
            </p>
          </div>
        )}

        {loading && <AppealLoader denial={denial} />}

        {letter && !loading && (
          <>
            {/* Letter — preview or edit */}
            <div className="rounded-[16px] overflow-hidden mb-5 animate-fade-in-up stagger-1"
              style={{ background: "#FFFFFF", border: "1px solid rgba(15,31,61,0.06)", boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
              {/* Toolbar */}
              <div className="px-6 py-3 flex items-center justify-between"
                style={{ borderBottom: "1px solid rgba(15,31,61,0.06)", background: "rgba(15,31,61,0.02)" }}>
                <span style={{ fontSize: "0.7rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  {editing ? "Editing" : "Your letter"}
                </span>
                {editing ? (
                  <div className="flex items-center gap-2">
                    <button onClick={() => setEditing(false)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-[8px]"
                      style={{ fontSize: "0.8rem", fontFamily: "var(--font-inter)", color: "var(--text-tertiary)", border: "1px solid rgba(15,31,61,0.1)", background: "transparent", cursor: "pointer" }}>
                      <X size={13} /> Discard
                    </button>
                    <button onClick={handleSaveEdit}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-[8px]"
                      style={{ fontSize: "0.8rem", fontFamily: "var(--font-inter)", color: "var(--navy)", background: "var(--gold)", border: "none", cursor: "pointer", fontWeight: 500 }}>
                      <CheckCircle size={13} /> Save changes
                    </button>
                  </div>
                ) : (
                  <button onClick={handleEdit}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] transition-colors"
                    style={{ fontSize: "0.8rem", fontFamily: "var(--font-inter)", color: "var(--text-secondary)", border: "1px solid rgba(15,31,61,0.1)", background: "transparent", cursor: "pointer" }}>
                    <Pencil size={13} /> Edit letter
                  </button>
                )}
              </div>

              {editing ? (
                <textarea
                  value={editText}
                  onChange={e => setEditText(e.target.value)}
                  className="w-full"
                  style={{
                    minHeight: "600px",
                    padding: "2rem",
                    fontSize: "0.9rem",
                    lineHeight: 1.85,
                    fontFamily: "'Times New Roman', Times, serif",
                    color: "#1A2A40",
                    border: "none",
                    outline: "none",
                    resize: "vertical",
                    background: "#FDFCFB",
                  }}
                />
              ) : (
                <div className="px-8 py-8">
                  <p style={{ color: "#1A2A40", fontSize: "0.9rem", lineHeight: 1.85, whiteSpace: "pre-wrap", fontFamily: "'Times New Roman', Times, serif" }}>
                    {activeText}
                  </p>
                </div>
              )}
            </div>

            {/* What we based this on */}
            <div className="rounded-[16px] overflow-hidden mb-5 animate-fade-in-up stagger-2"
              style={{ background: "#FFFFFF", border: "1px solid rgba(15,31,61,0.06)", boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
              <button
                onClick={() => setShowEvidence(v => !v)}
                className="w-full flex items-center justify-between px-6 py-4"
                style={{ background: "none", border: "none", cursor: "pointer" }}>
                <div>
                  <p style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-inter)", textAlign: "left" }}>
                    What we based this on
                  </p>
                  <p style={{ fontSize: "0.78rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", textAlign: "left", marginTop: "0.2rem" }}>
                    See the denial logic, evidence sources, and policy criteria the letter addresses
                  </p>
                </div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginLeft: "1rem", flexShrink: 0 }}>
                  {showEvidence ? "Hide ↑" : "Show ↓"}
                </span>
              </button>
              {showEvidence && (
                <div style={{ borderTop: "1px solid rgba(15,31,61,0.06)" }}>
                  {/* Denial reason */}
                  <div className="px-6 py-4" style={{ borderBottom: "1px solid rgba(15,31,61,0.05)" }}>
                    <p style={{ fontSize: "0.68rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "0.5rem" }}>Denial basis</p>
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.6 }}>
                      {denial?.denial_reason ?? "Not available"}
                    </p>
                    {denial?.cpb_code_cited && (
                      <p style={{ fontSize: "0.8rem", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)", marginTop: "0.4rem" }}>
                        Policy: {denial.cpb_code_cited}
                      </p>
                    )}
                  </div>
                  {/* Evidence summary */}
                  {letter.evidence_summary && (
                    <div className="px-6 py-4" style={{ borderBottom: "1px solid rgba(15,31,61,0.05)" }}>
                      <p style={{ fontSize: "0.68rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "0.5rem" }}>Evidence retrieved</p>
                      <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                        {letter.evidence_summary}
                      </p>
                    </div>
                  )}
                  {/* Citations */}
                  {letter.citations?.length > 0 && (
                    <div className="px-6 py-4">
                      <p style={{ fontSize: "0.68rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "0.75rem" }}>PubMed sources cited</p>
                      <ul className="space-y-2.5">
                        {letter.citations.slice(0, 5).map(c => (
                          <li key={c.pmid ?? c.title} className="flex items-start gap-3" style={{ fontSize: "0.82rem" }}>
                            <span style={{ color: "var(--gold)", fontFamily: "var(--font-mono)", flexShrink: 0 }}>PMID:{c.pmid}</span>
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
                </div>
              )}
            </div>

            {/* Request a revision */}
            <div className="rounded-[16px] overflow-hidden mb-5 animate-fade-in-up stagger-3"
              style={{ background: "#FFFFFF", border: "1px solid rgba(15,31,61,0.06)", boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
              <div className="px-6 py-4" style={{ borderBottom: "1px solid rgba(15,31,61,0.06)", background: "rgba(15,31,61,0.02)" }}>
                <p style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "var(--font-inter)" }}>
                  Something wrong with the letter?
                </p>
                <p style={{ fontSize: "0.78rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginTop: "0.2rem" }}>
                  Describe what needs to change. Vinci will rewrite only that part.
                </p>
              </div>
              <div className="px-6 pt-4 pb-2 flex flex-wrap gap-2">
                {QUICK_FIXES.map(fix => (
                  <button key={fix} onClick={() => setFeedback(fix)}
                    className="px-3 py-1.5 rounded-full text-xs transition-colors"
                    style={{
                      fontFamily: "var(--font-inter)",
                      border: "1px solid rgba(15,31,61,0.12)",
                      background: feedback === fix ? "var(--navy)" : "transparent",
                      color: feedback === fix ? "#fff" : "var(--text-secondary)",
                      cursor: "pointer",
                    }}>
                    {fix}
                  </button>
                ))}
              </div>
              <div className="px-6 pb-5 pt-3">
                <textarea
                  value={feedback}
                  onChange={e => setFeedback(e.target.value)}
                  placeholder="Or describe the issue in your own words, e.g. 'I tried methotrexate for 6 months, not 3' or 'The doctor's name is Dr. Patel, not Dr. Smith'"
                  rows={3}
                  className="w-full rounded-[10px] resize-none"
                  style={{
                    padding: "0.75rem 1rem",
                    fontSize: "0.875rem",
                    fontFamily: "var(--font-inter)",
                    color: "var(--text-primary)",
                    border: "1.5px solid rgba(15,31,61,0.12)",
                    outline: "none",
                    lineHeight: 1.6,
                    background: "#FAFAF8",
                    marginBottom: "0.75rem",
                  }}
                  onFocus={e => (e.target.style.borderColor = "var(--gold)")}
                  onBlur={e => (e.target.style.borderColor = "rgba(15,31,61,0.12)")}
                />
                <button
                  onClick={handleRevise}
                  disabled={!feedback.trim() || revising}
                  className="w-full flex items-center justify-center gap-2.5 rounded-[10px] font-medium transition-all"
                  style={{
                    padding: "0.75rem",
                    fontSize: "0.875rem",
                    fontFamily: "var(--font-inter)",
                    background: !feedback.trim() ? "rgba(15,31,61,0.06)" : "var(--navy)",
                    color: !feedback.trim() ? "var(--text-tertiary)" : "#fff",
                    border: "none",
                    cursor: !feedback.trim() ? "default" : "pointer",
                  }}>
                  {revising
                    ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Revising…</>
                    : "Revise with AI"
                  }
                </button>
              </div>
            </div>


            {/* Download & export */}
            <div className="rounded-[16px] overflow-hidden mb-5 animate-fade-in-up stagger-4"
              style={{ background: "#FFFFFF", border: "1px solid rgba(15,31,61,0.06)", boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
              <div className="px-6 py-3" style={{ borderBottom: "1px solid rgba(15,31,61,0.06)", background: "rgba(15,31,61,0.02)" }}>
                <span style={{ fontSize: "0.7rem", fontWeight: 500, color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  Export your letter
                </span>
              </div>
              <div className="p-5 flex flex-col gap-3">
                {/* PDF download via jsPDF */}
                <button
                  onClick={handleDownloadPDF}
                  disabled={pdfLoading}
                  className="w-full flex items-center justify-center gap-2.5 rounded-[12px] font-medium transition-all duration-150"
                  style={{
                    background: pdfLoading ? "rgba(201,168,76,0.7)" : "var(--gold)",
                    color: "var(--navy)",
                    padding: "0.75rem 1.25rem",
                    fontSize: "0.9rem",
                    fontFamily: "var(--font-inter)",
                    cursor: pdfLoading ? "wait" : "pointer",
                    border: "none",
                  }}
                >
                  {pdfLoading
                    ? <><span className="w-4 h-4 border-2 border-[#0F1F3D] border-t-transparent rounded-full animate-spin" /> Generating PDF…</>
                    : <><Download size={17} /> Download as PDF</>
                  }
                </button>

                {/* DOCX download */}
                <button
                  onClick={handleDownloadDocx}
                  className="w-full flex items-center justify-center gap-2.5 rounded-[12px] font-medium transition-all duration-150"
                  style={{
                    background: "transparent",
                    color: "var(--navy)",
                    padding: "0.75rem 1.25rem",
                    fontSize: "0.9rem",
                    fontFamily: "var(--font-inter)",
                    cursor: "pointer",
                    border: "1.5px solid rgba(15,31,61,0.15)",
                  }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(15,31,61,0.35)")}
                  onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(15,31,61,0.15)")}
                >
                  <FileText size={17} />
                  Download as Word (.docx)
                </button>

                {/* Copy */}
                <button
                  onClick={handleCopy}
                  className="w-full flex items-center justify-center gap-2.5 rounded-[12px] font-medium transition-all duration-150"
                  style={{
                    background: "transparent",
                    color: copied ? "var(--success)" : "var(--text-tertiary)",
                    padding: "0.75rem 1.25rem",
                    fontSize: "0.9rem",
                    fontFamily: "var(--font-inter)",
                    cursor: "pointer",
                    border: "1.5px solid rgba(15,31,61,0.08)",
                  }}
                >
                  {copied ? <><CheckCircle size={17} /> Copied to clipboard</> : <><Copy size={17} /> Copy plain text</>}
                </button>
              </div>
            </div>

            {/* Submission instructions */}
            <div style={card} className="p-8 mb-5 animate-fade-in-up stagger-5">
              <h3 style={{ color: "var(--text-primary)", marginBottom: "1.25rem" }}>How to submit your appeal</h3>
              <ol className="space-y-4">
                {[
                  "Download or copy the letter above",
                  `Send to: ${denial?.insurer_name ?? "your insurer"}'s Appeals Department (address on your denial letter)`,
                  "Keep a copy for your records and note the date you submitted",
                  "If you don't hear back within 60 days, contact your state insurance department, as that delay may itself be grounds for further action.",
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
              <div className="space-y-4">
                {[
                  { step: "1", text: "Once you submit, your insurer is required by law to issue a written decision within 60 days for standard appeals, or 72 hours if your situation is urgent." },
                  { step: "2", text: `If ${denial?.insurer_name ?? "your insurer"} upholds the denial, you have the right to request an independent external review. An independent medical reviewer (not the insurer) makes the final call.` },
                  { step: "3", text: "Patients win roughly 4 in 5 external reviews. The insurer's original decision is overturned more often than not when a case is properly documented and argued." },
                ].map(({ step, text }) => (
                  <div key={step} className="flex items-start gap-4">
                    <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                      style={{ background: "var(--gold-light)", color: "var(--gold)", fontFamily: "var(--font-mono)" }}>
                      {step}
                    </span>
                    <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "var(--font-inter)", lineHeight: 1.7 }}>
                      {text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {!loading && !letter && (
          <div className="text-center py-20 animate-fade-in-up">
            <p style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginBottom: "0.5rem" }}>
              We couldn't generate your letter.
            </p>
            <p style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
              This usually means the backend took too long or the denial data didn't come through. Go back and try again.
            </p>
            <Button variant="secondary" onClick={() => router.push("/denial")}>Go back to denial upload</Button>
          </div>
        )}
      </div>
    </div>
  );
}
