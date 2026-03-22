import Link from "next/link";
import { FileSearch, FileText, Scale, TrendingUp, Upload, Zap, CheckCircle, Shield } from "lucide-react";

const features = [
  { icon: FileSearch, title: "CPB Claim Matching",          body: "We match your procedure to your insurer's exact coverage criteria before you submit." },
  { icon: FileText,   title: "Denial Letter Parsing",       body: "Upload any denial letter — PDF, image, or doc — and we extract every critical detail instantly." },
  { icon: Scale,      title: "Evidence-Backed Appeals",     body: "We pull PubMed studies, FDA approvals, and CMS coverage data to build your appeal automatically." },
  { icon: TrendingUp, title: "Financial Impact Simulation", body: "See exactly what the denial costs you over 12 months — and what winning saves." },
];

const steps = [
  { icon: Upload,      n: "1", label: "We read your denial",  sub: "Upload any format — we extract every detail" },
  { icon: Zap,         n: "2", label: "We check their rules", sub: "We match your case to their own coverage policy" },
  { icon: CheckCircle, n: "3", label: "We write your appeal", sub: "Evidence-backed, addressed to the right place" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 z-40 bg-slate-950/80 backdrop-blur border-b border-slate-800/60">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-lg">
            <Shield size={20} className="text-[#C9A84C]" />
            <span>Vinci</span>
          </div>
          <Link href="/role" className="px-4 py-1.5 bg-[#C9A84C] text-[#0F1F3D] font-semibold rounded-lg text-sm hover:bg-[#E4C97A] transition-colors">
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-24 px-4 text-center max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#C9A84C]/10 border border-[#C9A84C]/20 text-[#C9A84C] text-xs font-medium mb-8">
          <Shield size={12} />
          Prior authorization appeals, automated
        </div>
        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight leading-tight mb-6">
          Your insurer said no.<br />
          <span className="text-emerald-400">We&apos;ll help you fight back.</span>
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Vinci matches your claim to insurer policies, parses denial letters, generates evidence-backed appeal letters, and shows you exactly what&apos;s at stake financially.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/role?as=patient" className="min-h-[52px] px-8 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold rounded-xl transition-all hover:scale-[1.02] text-center flex items-center justify-center">
            I&apos;m a Patient
          </Link>
          <Link href="/role?as=doctor" className="min-h-[52px] px-8 py-3 border border-slate-600 hover:border-slate-400 text-slate-200 font-semibold rounded-xl transition-all hover:bg-slate-800/50 text-center flex items-center justify-center">
            I&apos;m a Doctor
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 max-w-6xl mx-auto">
        <h2 className="text-center text-slate-500 text-sm font-medium uppercase tracking-widest mb-10">What Vinci does for you</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map(({ icon: Icon, title, body }) => (
            <div key={title} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-colors">
              <div className="w-10 h-10 rounded-xl bg-[#C9A84C]/10 flex items-center justify-center mb-4">
                <Icon size={20} className="text-[#C9A84C]" />
              </div>
              <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 max-w-4xl mx-auto">
        <h2 className="text-center text-slate-500 text-sm font-medium uppercase tracking-widest mb-12">How it works</h2>
        <div className="flex flex-col sm:flex-row items-start gap-8">
          {steps.map(({ icon: Icon, n, label, sub }, i) => (
            <div key={n} className="flex-1 flex flex-col items-center text-center relative">
              {i < steps.length - 1 && <div className="hidden sm:block absolute top-5 left-[calc(50%+2.5rem)] right-0 h-px bg-slate-800" />}
              <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-sm mb-4 z-10">
                {n}
              </div>
              <Icon size={20} className="text-slate-400 mb-3" />
              <p className="font-semibold text-slate-200 mb-1">{label}</p>
              <p className="text-sm text-slate-500">{sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 px-4 border-y border-slate-800/60">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row gap-8 items-center justify-center text-center">
          {[
            ["70%",   "of denials like these are overturned on appeal", "— KFF 2024"],
            ["$4,080","average annual cost when patients pay out of pocket", "— HCUP 2023"],
            ["<60s",  "to submit an appeal letter with Vinci", ""],
          ].map(([stat, label, attr]) => (
            <div key={stat} className="flex-1">
              <p className="text-3xl font-bold text-[#C9A84C]">{stat}</p>
              <p className="text-sm text-slate-400 mt-1">{label}</p>
              {attr && <p className="text-xs text-slate-600 mt-0.5">{attr}</p>}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 text-center max-w-2xl mx-auto">
        <h2 className="text-3xl font-bold mb-4">Ready to fight your denial?</h2>
        <p className="text-slate-400 mb-8">Upload your denial letter and we&apos;ll take it from there.</p>
        <Link href="/denial" className="inline-flex min-h-[52px] px-10 py-3 items-center bg-[#C9A84C] text-[#0F1F3D] font-bold rounded-xl hover:bg-[#E4C97A] transition-all hover:scale-[1.02]">
          Upload my denial letter →
        </Link>
      </section>

      <footer className="py-8 px-4 border-t border-slate-800/60 text-center text-xs text-slate-600">
        Vinci is a decision-support tool. Always consult a healthcare provider.
      </footer>
    </div>
  );
}
