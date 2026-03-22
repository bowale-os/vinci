// ─── Claim Matching ───────────────────────────────────────────────────────────

export interface ClaimSubmission {
  cpt_code: string;
  icd10_codes: string[];
  insurer_id: string;
  patient_dob: string;
  clinical_notes: string;
}

export interface CPBMatchResult {
  match_score: number; // 0–100
  matched_criteria: string[];
  missing_criteria: string[];
  suggestions: string[];
  cpb_policy_id: string;
  cpb_summary: string;
}

export interface Insurer {
  id: string;
  name: string;
  cpb_policy_id: string;
}

// ─── Denial Parsing ───────────────────────────────────────────────────────────

export interface DenialParseResult {
  patient_name: string;
  claim_id: string;
  denial_reason: string;
  cpb_code_cited: string;
  deadline: string; // ISO date
  required_docs: string[];
  insurer_name: string;
  denial_date?: string;
  service_denied?: string;
  denial_codes?: string[];
  tldr: string;
  raw_text: string;
}

// ─── Appeal Letter ────────────────────────────────────────────────────────────

export interface Citation {
  title: string;
  url: string;
  pmid?: string;
}

export interface FDAReference {
  product: string;
  approval_date: string;
}

export interface AppealLetter {
  letter_text: string;
  citations: Citation[];
  fda_references: FDAReference[];
  generated_at: string; // ISO timestamp
}

export interface AppealRequest {
  denial: DenialParseResult;
  cpt_code: string;
  clinical_notes: string;
}

// ─── Financial Simulation ─────────────────────────────────────────────────────

export interface MonthlyOption {
  months: number;
  payment: number;
}

export interface AccountImpact {
  account_id: string;
  balance_after: number;
}

export interface FinancialSimulation {
  procedure_cost: number;
  patient_responsibility: number;
  deductible_remaining: number;
  oop_max_remaining: number;
  monthly_options: MonthlyOption[];
  account_impact: AccountImpact[];
}

export interface FinancialRequest {
  procedure_cost: number;
  deductible_remaining: number;
  oop_max: number;
  plan_type: string;
}

// ─── App State ────────────────────────────────────────────────────────────────

export type UserRole = "patient" | "doctor";

export interface PACase {
  id: string;
  procedure: string;
  insurer: string;
  status: "pending" | "approved" | "denied" | "appealing";
  deadline: string;
  cpt_code: string;
}
