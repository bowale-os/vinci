"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { Stethoscope, User, ArrowRight, Shield } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import type { UserRole } from "@/types";

function RolePageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const { setRole } = useVinci();

  const select = (r: UserRole) => {
    setRole(r);
    router.push("/denial");
  };

  const as = params.get("as");
  useEffect(() => {
    if (as === "patient" || as === "doctor") {
      select(as as UserRole);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [as]);

  if (as === "patient" || as === "doctor") return null;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-4">
      <div className="flex items-center gap-2 mb-10">
        <Shield size={22} className="text-[#C9A84C]" />
        <span className="font-bold text-xl">Vinci</span>
      </div>
      <h1 className="text-3xl font-bold text-center mb-3">Who are you here for?</h1>
      <p className="text-slate-400 text-center mb-10 max-w-sm">We tailor the experience based on your role.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 w-full max-w-lg">
        {([
          { role: "patient" as UserRole, Icon: User,          label: "I'm a Patient",  sub: "I received a denial and need help appealing it." },
          { role: "doctor"  as UserRole, Icon: Stethoscope,   label: "I'm a Doctor",   sub: "I'm helping a patient navigate their prior auth." },
        ]).map(({ role, Icon, label, sub }) => (
          <button key={role} onClick={() => select(role)}
            className="group flex flex-col items-start gap-4 p-6 bg-slate-900 border border-slate-800 rounded-2xl hover:border-[#C9A84C]/50 hover:bg-slate-900/80 transition-all text-left">
            <div className="w-12 h-12 rounded-xl bg-[#C9A84C]/10 flex items-center justify-center group-hover:bg-[#C9A84C]/20 transition-colors">
              <Icon size={22} className="text-[#C9A84C]" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-slate-100 mb-1">{label}</p>
              <p className="text-sm text-slate-500">{sub}</p>
            </div>
            <ArrowRight size={16} className="text-slate-600 group-hover:text-[#C9A84C] transition-colors self-end" />
          </button>
        ))}
      </div>
    </div>
  );
}

export default function RolePage() {
  return <Suspense><RolePageInner /></Suspense>;
}
