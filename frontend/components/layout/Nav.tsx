"use client";
import Link from "next/link";
import { useState } from "react";
import { Menu, X, Shield } from "lucide-react";

export function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 inset-x-0 z-40 bg-slate-950/80 backdrop-blur border-b border-slate-800/60">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg tracking-tight">
          <Shield size={20} className="text-[#C9A84C]" />
          <span className="text-white">Vinci</span>
        </Link>

        {/* Desktop */}
        <div className="hidden sm:flex items-center gap-6 text-sm text-slate-400">
          <Link href="/denial" className="hover:text-white transition-colors">Upload Denial</Link>
          <Link href="/appeal/letter" className="hover:text-white transition-colors">My Letter</Link>
          <Link href="/role" className="px-4 py-1.5 bg-[#C9A84C] text-[#0F1F3D] font-semibold rounded-lg hover:bg-[#E4C97A] transition-colors">Get Started</Link>
        </div>

        {/* Mobile */}
        <button className="sm:hidden text-slate-400 hover:text-white p-1" onClick={() => setOpen(o => !o)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="sm:hidden bg-slate-900 border-t border-slate-800 px-4 py-4 flex flex-col gap-3">
          <Link href="/denial" className="text-slate-300 py-2" onClick={() => setOpen(false)}>Upload Denial</Link>
          <Link href="/appeal/letter" className="text-slate-300 py-2" onClick={() => setOpen(false)}>My Letter</Link>
          <Link href="/role" className="py-2.5 text-center bg-[#C9A84C] text-[#0F1F3D] font-semibold rounded-xl" onClick={() => setOpen(false)}>Get Started</Link>
        </div>
      )}
    </nav>
  );
}
