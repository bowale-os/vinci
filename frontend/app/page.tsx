import Link from "next/link";
import { FileSearch, FileText, Scale, TrendingUp, Upload, Zap, CheckCircle, Shield } from "lucide-react";

const features = [
  { icon: FileSearch, title: "CPB Claim Matching",          body: "We match your procedure to your insurer's exact coverage criteria before you submit." },
  { icon: FileText,   title: "Denial Letter Parsing",       body: "Upload any denial letter — PDF, image, or doc — and we extract every critical detail instantly." },
  { icon: Scale,      title: "Evidence-Backed Appeals",     body: "We pull PubMed studies, FDA approvals, and CMS coverage data to build your appeal automatically." },
  { icon: TrendingUp, title: "Financial Impact Simulation", body: "See exactly what the denial costs you over 12 months — and what winning saves." },
];

const steps = [
  { n: "01", label: "We read your denial",  sub: "Upload any format — we extract every detail" },
  { n: "02", label: "We check their rules", sub: "We match your case to their own coverage policy" },
  { n: "03", label: "We write your appeal", sub: "Evidence-backed, addressed to the right place" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen" style={{ background: "var(--warm-white)" }}>

      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 z-40 bg-[#0F1F3D] border-b border-white/8">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-white"
            style={{ fontFamily: "var(--font-jakarta)", fontWeight: 700, letterSpacing: "-0.02em", fontSize: "1.1rem" }}>
            <Shield size={18} className="text-[#C9A84C]" strokeWidth={2.5} />
            Vinci
          </div>
          <Link href="/role"
            className="px-5 py-2 text-sm font-semibold rounded-[12px] bg-[#C9A84C] text-[#0F1F3D] hover:scale-[1.02] transition-transform duration-150"
            style={{ fontFamily: "var(--font-inter)" }}>
            Get started
          </Link>
        </div>
      </nav>

      {/* ── Hero — navy ─────────────────────────────────────── */}
      <section className="bg-[#0F1F3D] pt-40 pb-32 px-6">
        <div className="max-w-[1200px] mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-10 animate-fade-in-up"
            style={{
              background: "rgba(201,168,76,0.12)",
              border: "1px solid rgba(201,168,76,0.25)",
              color: "#C9A84C",
              fontFamily: "var(--font-inter)",
              letterSpacing: "0.04em",
              textTransform: "uppercase",
            }}>
            <Shield size={11} />
            Prior authorization appeals, automated
          </div>

          <h1 className="text-white mb-6 animate-fade-in-up stagger-1" style={{ maxWidth: "14ch" }}>
            Your insurer said no.<br />
            <span style={{ color: "#C9A84C" }}>We'll help you fight back.</span>
          </h1>

          <p className="text-white/60 mb-10 animate-fade-in-up stagger-2"
            style={{ maxWidth: "55ch", fontSize: "1.125rem", fontFamily: "var(--font-inter)", lineHeight: 1.7 }}>
            Vinci matches your claim to insurer policies, parses denial letters, generates evidence-backed appeal letters,
            and shows you exactly what's at stake financially.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 animate-fade-in-up stagger-3">
            <Link href="/role?as=patient"
              className="inline-flex items-center justify-center min-h-[52px] px-8 text-base font-semibold rounded-[12px] bg-[#C9A84C] text-[#0F1F3D] hover:scale-[1.02] active:scale-[0.98] transition-transform duration-150"
              style={{ fontFamily: "var(--font-inter)" }}>
              I&apos;m a Patient
            </Link>
            <Link href="/role?as=doctor"
              className="inline-flex items-center justify-center min-h-[52px] px-8 text-base font-semibold rounded-[12px] text-white hover:bg-white/8 transition-colors duration-150"
              style={{ border: "1.5px solid rgba(255,255,255,0.25)", fontFamily: "var(--font-inter)" }}>
              I&apos;m a Doctor
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features — warm-white ────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "var(--warm-white)" }}>
        <div className="max-w-[1200px] mx-auto">
          <p className="text-xs font-medium uppercase tracking-widest mb-12 text-center"
            style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.08em" }}>
            What Vinci does for you
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map(({ icon: Icon, title, body }, i) => (
              <div key={title}
                className={`bg-white rounded-[16px] p-8 transition-all duration-200 hover:shadow-[0_8px_24px_rgba(15,31,61,0.10)] hover:-translate-y-0.5 animate-fade-in-up stagger-${i + 1}`}
                style={{ border: "1px solid rgba(15,31,61,0.06)", boxShadow: "0 2px 8px rgba(15,31,61,0.06)" }}>
                <div className="w-10 h-10 rounded-[10px] flex items-center justify-center mb-6"
                  style={{ background: "var(--gold-light)" }}>
                  <Icon size={19} style={{ color: "var(--gold)" }} />
                </div>
                <h3 className="mb-2" style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{title}</h3>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.65, fontFamily: "var(--font-inter)" }}>
                  {body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works — warm-white ────────────────────────── */}
      <section className="py-24 px-6 border-t" style={{ borderColor: "rgba(15,31,61,0.06)" }}>
        <div className="max-w-[1200px] mx-auto">
          <p className="text-xs font-medium uppercase tracking-widest mb-16 text-center"
            style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", letterSpacing: "0.08em" }}>
            How it works
          </p>

          <div className="flex flex-col sm:flex-row items-start gap-8 max-w-3xl mx-auto">
            {steps.map(({ n, label, sub }, i) => (
              <div key={n} className={`flex-1 relative animate-fade-in-up stagger-${i + 1}`}>
                {i < steps.length - 1 && (
                  <div className="hidden sm:block absolute top-4 left-[calc(50%+2rem)] right-0 h-px"
                    style={{ background: "rgba(15,31,61,0.10)" }} />
                )}
                <div className="flex flex-col items-center text-center">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center mb-6 z-10 relative"
                    style={{
                      background: "var(--gold-light)",
                      border: "1px solid var(--gold-border)",
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.75rem",
                      fontWeight: 500,
                      color: "var(--gold)",
                    }}>
                    {n}
                  </div>
                  <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 600, fontSize: "0.975rem", color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                    {label}
                  </p>
                  <p style={{ fontSize: "0.875rem", color: "var(--text-tertiary)", lineHeight: 1.5, fontFamily: "var(--font-inter)" }}>
                    {sub}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats — navy ─────────────────────────────────────── */}
      <section className="py-20 px-6 bg-[#0F1F3D]">
        <div className="max-w-[1200px] mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            {[
              { stat: "70%",    label: "of denials like these are overturned on appeal",       attr: "— KFF 2024" },
              { stat: "$4,080", label: "average annual cost when patients pay out of pocket",  attr: "— HCUP 2023" },
              { stat: "<60s",   label: "to submit an appeal letter with Vinci",                attr: "" },
            ].map(({ stat, label, attr }) => (
              <div key={stat} className="animate-fade-in-up">
                <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 800, fontSize: "2.5rem", color: "#C9A84C", letterSpacing: "-0.03em" }}>
                  {stat}
                </p>
                <p style={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.55)", marginTop: "0.5rem", fontFamily: "var(--font-inter)", maxWidth: "28ch", margin: "0.5rem auto 0" }}>
                  {label}
                </p>
                {attr && (
                  <p style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.28)", marginTop: "0.25rem", fontFamily: "var(--font-inter)" }}>
                    {attr}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA — warm-white ─────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "var(--warm-white)" }}>
        <div className="max-w-[600px] mx-auto text-center">
          <h2 style={{ color: "var(--text-primary)", marginBottom: "1rem" }}>Ready to fight your denial?</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2.5rem", maxWidth: "50ch", margin: "0 auto 2.5rem", fontFamily: "var(--font-inter)" }}>
            Upload your denial letter and we&apos;ll take it from there.
          </p>
          <Link href="/denial"
            className="inline-flex items-center min-h-[52px] px-10 text-base font-semibold rounded-[12px] bg-[#C9A84C] text-[#0F1F3D] hover:scale-[1.02] active:scale-[0.98] transition-transform duration-150"
            style={{ fontFamily: "var(--font-inter)" }}>
            Upload my denial letter →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-6 bg-[#0F1F3D] border-t border-white/8">
        <div className="max-w-[1200px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-white/70"
            style={{ fontFamily: "var(--font-jakarta)", fontWeight: 700, letterSpacing: "-0.015em" }}>
            <Shield size={16} className="text-[#C9A84C]" />
            Vinci
          </div>
          <p style={{ fontSize: "0.8rem", color: "rgba(255,255,255,0.35)", fontFamily: "var(--font-inter)" }}>
            Vinci is a decision-support tool. Always consult a healthcare provider.
          </p>
        </div>
      </footer>

    </div>
  );
}
