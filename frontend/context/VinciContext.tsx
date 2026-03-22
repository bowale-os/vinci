"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import type { DenialParseResult, AppealLetter, FinancialSimulationResult, UserRole } from "@/types";

interface VinciState {
  role: UserRole | null;
  denial: DenialParseResult | null;
  appeal: AppealLetter | null;
  financial: FinancialSimulationResult | null;
  cptCode: string;
  clinicalNotes: string;
  patientState: string;
  setRole: (r: UserRole) => void;
  setDenial: (d: DenialParseResult) => void;
  setAppeal: (a: AppealLetter) => void;
  setFinancial: (f: FinancialSimulationResult) => void;
  setCptCode: (c: string) => void;
  setClinicalNotes: (n: string) => void;
  setPatientState: (s: string) => void;
}

const VinciContext = createContext<VinciState | null>(null);

export function VinciProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<UserRole | null>(null);
  const [denial, setDenialState] = useState<DenialParseResult | null>(null);
  const [appeal, setAppealState] = useState<AppealLetter | null>(null);
  const [financial, setFinancialState] = useState<FinancialSimulationResult | null>(null);
  const [cptCode, setCptCodeState] = useState("");
  const [clinicalNotes, setClinicalNotesState] = useState("");
  const [patientState, setPatientStateState] = useState("CA");

  // Persist to sessionStorage
  useEffect(() => {
    const saved = sessionStorage.getItem("vinci_state");
    if (saved) {
      try {
        const s = JSON.parse(saved);
        if (s.role) setRoleState(s.role);
        if (s.denial) setDenialState(s.denial);
        if (s.appeal) setAppealState(s.appeal);
        if (s.financial) setFinancialState(s.financial);
        if (s.cptCode) setCptCodeState(s.cptCode);
        if (s.clinicalNotes) setClinicalNotesState(s.clinicalNotes);
        if (s.patientState) setPatientStateState(s.patientState);
      } catch {}
    }
  }, []);

  const persist = (update: Partial<VinciState>) => {
    const current = (() => { try { return JSON.parse(sessionStorage.getItem("vinci_state") || "{}"); } catch { return {}; } })();
    sessionStorage.setItem("vinci_state", JSON.stringify({ ...current, ...update }));
  };

  const setRole = (r: UserRole) => { setRoleState(r); persist({ role: r }); };
  const setDenial = (d: DenialParseResult) => { setDenialState(d); persist({ denial: d }); };
  const setAppeal = (a: AppealLetter) => { setAppealState(a); persist({ appeal: a }); };
  const setFinancial = (f: FinancialSimulationResult) => { setFinancialState(f); persist({ financial: f }); };
  const setCptCode = (c: string) => { setCptCodeState(c); persist({ cptCode: c }); };
  const setClinicalNotes = (n: string) => { setClinicalNotesState(n); persist({ clinicalNotes: n }); };
  const setPatientState = (s: string) => { setPatientStateState(s); persist({ patientState: s }); };

  return (
    <VinciContext.Provider value={{
      role, denial, appeal, financial, cptCode, clinicalNotes, patientState,
      setRole, setDenial, setAppeal, setFinancial, setCptCode, setClinicalNotes, setPatientState,
    }}>
      {children}
    </VinciContext.Provider>
  );
}

export function useVinci() {
  const ctx = useContext(VinciContext);
  if (!ctx) throw new Error("useVinci must be used within VinciProvider");
  return ctx;
}
