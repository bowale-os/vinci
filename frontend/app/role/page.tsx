"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { Stethoscope, User, ArrowRight, Shield } from "lucide-react";
import { useVinci } from "@/context/VinciContext";
import type { UserRole } from "@/types";

const cardStyle = {
  background: "#FFFFFF",
  border: "1px solid rgba(15,31,61,0.08)",
  borderRadius: "16px",
  boxShadow: "0 2px 8px rgba(15,31,61,0.06)",
  transition: "box-shadow 200ms ease, transform 200ms ease, border-color 200ms ease",
};

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
    <div className="min-h-screen flex flex-col items-center justify-center px-6" style={{ background: "var(--warm-white)" }}>

      {/* Logo */}
      <div className="flex items-center gap-2 mb-12 animate-fade-in-up"
        style={{ fontFamily: "var(--font-jakarta)", fontWeight: 700, fontSize: "1.2rem", color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
        <Shield size={20} className="text-[#C9A84C]" strokeWidth={2.5} />
        Vinci
      </div>

      {/* Heading */}
      <h1 className="text-center mb-3 animate-fade-in-up stagger-1" style={{ color: "var(--text-primary)" }}>
        Who are you here for?
      </h1>
      <p className="text-center mb-12 animate-fade-in-up stagger-2"
        style={{ color: "var(--text-secondary)", maxWidth: "38ch", fontFamily: "var(--font-inter)" }}>
        We tailor the experience based on your role.
      </p>

      {/* Role cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-lg animate-fade-in-up stagger-3">
        {([
          { role: "patient" as UserRole, Icon: User,        label: "I'm a Patient", sub: "I received a denial and need help appealing it." },
          { role: "doctor"  as UserRole, Icon: Stethoscope, label: "I'm a Doctor",  sub: "I'm helping a patient navigate their prior auth." },
        ]).map(({ role, Icon, label, sub }) => (
          <button
            key={role}
            onClick={() => select(role)}
            className="group flex flex-col items-start gap-5 p-8 text-left"
            style={cardStyle}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.boxShadow = "0 8px 24px rgba(15,31,61,0.10)";
              (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(201,168,76,0.40)";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 8px rgba(15,31,61,0.06)";
              (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(15,31,61,0.08)";
            }}
          >
            <div className="w-12 h-12 rounded-[12px] flex items-center justify-center"
              style={{ background: "var(--gold-light)" }}>
              <Icon size={22} style={{ color: "var(--gold)" }} />
            </div>
            <div className="flex-1">
              <p style={{ fontFamily: "var(--font-jakarta)", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.375rem" }}>
                {label}
              </p>
              <p style={{ fontSize: "0.875rem", color: "var(--text-tertiary)", fontFamily: "var(--font-inter)", lineHeight: 1.55 }}>
                {sub}
              </p>
            </div>
            <ArrowRight size={15} style={{ color: "var(--text-tertiary)", alignSelf: "flex-end" }} />
          </button>
        ))}
      </div>

    </div>
  );
}

export default function RolePage() {
  return <Suspense><RolePageInner /></Suspense>;
}
