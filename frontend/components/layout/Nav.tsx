"use client";
import Link from "next/link";
import { useState } from "react";
import { Menu, X, Shield } from "lucide-react";

export function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 inset-x-0 z-40 bg-[#0F1F3D] border-b border-white/8">
      <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 font-display font-700 text-lg tracking-tight text-white">
          <Shield size={18} className="text-[#C9A84C]" strokeWidth={2.5} />
          <span style={{ fontFamily: "var(--font-jakarta)", fontWeight: 700, letterSpacing: "-0.02em" }}>Vinci</span>
        </Link>

        {/* Desktop */}
        <div className="hidden sm:flex items-center gap-8">
          <Link href="/denial" className="text-sm text-white/60 hover:text-white transition-colors duration-150">
            Upload Denial
          </Link>
          <Link href="/appeal/letter" className="text-sm text-white/60 hover:text-white transition-colors duration-150">
            My Letter
          </Link>
          <Link
            href="/role"
            className="px-5 py-2 bg-[#C9A84C] text-[#0F1F3D] text-sm font-semibold rounded-[12px] hover:scale-[1.02] transition-transform duration-150"
            style={{ fontFamily: "var(--font-inter)" }}
          >
            Get started
          </Link>
        </div>

        {/* Mobile toggle */}
        <button className="sm:hidden text-white/60 hover:text-white p-1 transition-colors" onClick={() => setOpen(o => !o)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="sm:hidden bg-[#0F1F3D] border-t border-white/8 px-6 py-5 flex flex-col gap-4">
          <Link href="/denial" className="text-sm text-white/70 py-1" onClick={() => setOpen(false)}>Upload Denial</Link>
          <Link href="/appeal/letter" className="text-sm text-white/70 py-1" onClick={() => setOpen(false)}>My Letter</Link>
          <Link
            href="/role"
            className="py-3 text-center text-sm bg-[#C9A84C] text-[#0F1F3D] font-semibold rounded-[12px]"
            onClick={() => setOpen(false)}
          >
            Get started
          </Link>
        </div>
      )}
    </nav>
  );
}
