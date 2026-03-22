"""
Seed clinical_guidelines from USPSTF API + hardcoded high-value society guidelines.

Sources:
  1. USPSTF (US Preventive Services Task Force) — free public API
  2. Hardcoded excerpts from AHA/ACC, AAOS, ACS, ADA guidelines
     for the top denial categories.
"""
import sys
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.snowflake_client import get_connection

USPSTF_API = "https://www.uspreventiveservicestaskforce.org/uspstf/uspsapi/recommendation-summary/all"

# Hardcoded society guidelines for top denial categories
SOCIETY_GUIDELINES = [
    # ── AAOS — Orthopedic ───────────────────────────────────────────────
    ("AAOS-TKA-2025", "AAOS", "Management of Osteoarthritis of the Knee (Non-Arthroplasty and TKA)",
     2025, "Musculoskeletal", ["27447", "27130"], ["M17.11", "M17.12"],
     """Strong Recommendation: Total knee arthroplasty (TKA) is recommended for patients with symptomatic moderate-to-severe osteoarthritis of the knee who have failed non-surgical management.
Non-surgical management should include: exercise therapy, weight management, NSAIDs, and may include intra-articular injections.
Strong Recommendation: TKA provides significant improvement in pain, function, and quality of life for appropriately selected patients.
Moderate Recommendation: Patients with radiographic evidence of severe joint space narrowing (Kellgren-Lawrence grade 3-4) and functional limitation are appropriate surgical candidates.
Evidence Grade: Strong (based on multiple RCTs and systematic reviews demonstrating consistent benefit).""",
     "A"),

    ("AAOS-SPINE-2022", "AAOS", "Clinical Practice Guideline for Lumbar Spinal Fusion",
     2022, "Musculoskeletal", ["22612", "22630", "22614"], ["M43.16", "M47.816"],
     """Strong Recommendation: Lumbar spinal fusion is recommended for patients with symptomatic degenerative spondylolisthesis with spinal stenosis who have failed conservative treatment.
Moderate Recommendation: Fusion improves outcomes compared to non-operative care for selected patients with: instability, neurological compromise, or structural deformity.
Conservative treatment of at least 3 months is recommended before surgical intervention for non-urgent cases.
Strong Recommendation: Patient selection should include MRI confirmation of neural compression correlating with symptoms.
Evidence Grade: Moderate (multiple RCTs support fusion over non-operative care for degenerative spondylolisthesis).""",
     "B"),

    # ── ACC/AHA — Cardiology ────────────────────────────────────────────
    ("ACC-CATH-2021", "ACC/AHA", "Guideline for Coronary Artery Revascularization",
     2021, "Cardiovascular", ["93454", "93455", "93460"], ["I25.10", "I20.0"],
     """Class I Recommendation (Strong): Coronary angiography is recommended in patients with: suspected ACS with high-risk features, stable ischemic heart disease with unacceptable symptoms despite optimal medical therapy, or pre-operative evaluation for high-risk non-cardiac surgery.
Class I: Diagnostic cardiac catheterization is the gold standard for coronary artery disease assessment when non-invasive testing is inconclusive or positive.
Class IIa: Coronary angiography is reasonable for patients with intermediate-high pretest probability of obstructive CAD and intermediate-risk stress test findings.
Evidence Grade: Level A (based on multiple RCTs and large observational studies).""",
     "A"),

    # ── ADA — Diabetes ──────────────────────────────────────────────────
    ("ADA-CGM-2025", "American Diabetes Association", "Standards of Care in Diabetes 2025 — CGM",
     2025, "Endocrinology", ["95251", "95250"], ["E11.65", "E10.65"],
     """Strong Recommendation (Level A): Real-time CGM is recommended for all adults with type 1 diabetes using multiple daily injections or continuous subcutaneous insulin infusion to improve HbA1c and reduce hypoglycemia.
Strong Recommendation (Level A): Real-time CGM should be offered to adults with type 2 diabetes on intensive insulin therapy to improve glycemic control.
Recommendation (Level B): Intermittent-scan CGM is a cost-effective alternative to real-time CGM for patients who prefer this option.
CGM metrics: Time in range (TIR) 70-180 mg/dL goal ≥70%; Time below range <70 mg/dL goal <4%.
Evidence supports CGM use in reducing HbA1c by 0.5-1.0% and reducing hypoglycemic events by 38-72% compared to self-monitoring of blood glucose.""",
     "A"),

    ("ADA-BARIATRIC-2025", "American Diabetes Association", "Standards of Care — Metabolic Surgery",
     2025, "Endocrinology", ["43644", "43645", "43770"], ["E11.9", "E66.01"],
     """Strong Recommendation (Level A): Metabolic surgery should be recommended for adults with T2DM and BMI ≥ 40 kg/m2 and for those with BMI 35-39.9 kg/m2 inadequately controlled by lifestyle and pharmacological therapy.
Recommendation (Level B): Metabolic surgery may be considered for adults with T2DM and BMI 30-34.9 kg/m2 if hyperglycemia is inadequately controlled despite optimal medical management.
Evidence: Randomized controlled trials demonstrate metabolic surgery superior to intensive medical therapy for T2DM remission, cardiovascular risk reduction, and quality of life.
Metabolic surgery reduces cardiovascular mortality by 40% and all-cause mortality by 30% in patients with T2DM and obesity.""",
     "A"),

    # ── AASM — Sleep Medicine ───────────────────────────────────────────
    ("AASM-OSA-2019", "American Academy of Sleep Medicine", "Clinical Practice Guideline for Diagnostic Testing of OSA in Adults",
     2019, "Pulmonology/Sleep", ["95810", "95811", "94660"], ["G47.33"],
     """Strong Recommendation: Polysomnography (PSG) is the standard diagnostic test for OSA and is recommended when sleep apnea or other sleep disorders are suspected.
Conditional Recommendation: Home sleep apnea testing (HSAT) may be used for the diagnosis of uncomplicated adult patients with high pretest probability of moderate-to-severe OSA.
Strong Recommendation: CPAP therapy is recommended for all patients with OSA (AHI ≥ 5) who have symptoms or cardiovascular comorbidities.
CPAP reduces AHI by >50% in most patients and improves: daytime sleepiness (ESS reduction 2.5 points), blood pressure (systolic 2-3 mmHg), and quality of life.
Evidence Grade: Strong for PSG as diagnostic standard; Conditional for HSAT in selected patients.""",
     "A"),

    # ── NCCN — Oncology ─────────────────────────────────────────────────
    ("NCCN-NGS-2025", "NCCN", "Next Generation Sequencing (NGS) — Oncology Testing",
     2025, "Oncology", ["81455", "81450", "81445"], ["C34.10", "C50.912", "C18.9"],
     """NCCN Category 1 Recommendation: Comprehensive biomarker testing is recommended for all patients with metastatic non-small cell lung cancer, including testing for EGFR, ALK, ROS1, BRAF, MET, RET, NTRK, PD-L1.
Category 1: Broad molecular profiling (NGS) is preferred over sequential single-gene testing to ensure all relevant biomarkers are identified in a timely fashion, particularly when tissue is limited.
Category 2A: NGS-based comprehensive genomic profiling recommended for: metastatic colorectal cancer (KRAS, NRAS, BRAF, MSI/MMR, HER2), metastatic breast cancer (PIK3CA, BRCA1/2, PD-L1, HER2), ovarian cancer (BRCA1/2, HRD), and prostate cancer (AR, BRCA1/2, MSI).
Evidence supports that biomarker-matched targeted therapy improves progression-free survival and overall survival compared to chemotherapy in biomarker-selected populations.""",
     "A"),

    ("NCCN-CHEMO-2025", "NCCN", "Antiemesis and Chemotherapy Administration Guidelines",
     2025, "Oncology", ["96413", "96415", "96417"], ["C34.10", "C50.912"],
     """NCCN Category 1: Chemotherapy administration according to NCCN guidelines represents the standard of care for treatment of malignancy.
NCCN Clinical Practice Guidelines in Oncology provide evidence-based, consensus-driven recommendations for cancer treatment.
Category 1 evidence level indicates: uniform NCCN consensus based on high-level evidence that the intervention is appropriate.
Category 2A evidence level indicates: uniform NCCN consensus based on lower-level evidence including clinical experience that the intervention is appropriate.
All NCCN-recommended regimens have demonstrated clinical benefit in peer-reviewed clinical trials and represent the standard against which new therapies are compared.""",
     "A"),

    # ── ACR — Rheumatology ──────────────────────────────────────────────
    ("ACR-BIO-2022", "American College of Rheumatology", "Guideline for Treatment of Rheumatoid Arthritis",
     2022, "Rheumatology", ["J0129", "J0135", "J3262"], ["M05.79", "M06.09"],
     """Strong Recommendation: Conventional synthetic DMARDs (csDMARDs), particularly methotrexate, are the preferred initial treatment for patients with moderate-to-high disease activity RA.
Strong Recommendation: For patients with moderate-to-high disease activity despite csDMARD therapy, addition of a biologic DMARD (bDMARD) or targeted synthetic DMARD (tsDMARD) is recommended.
Conditional Recommendation: TNF inhibitors, IL-6 receptor inhibitors, abatacept, and JAK inhibitors are all appropriate options for csDMARD-inadequate responders; choice based on comorbidities, cost, and patient preference.
Strong Recommendation: Treat-to-target strategy (goal: low disease activity or remission) is recommended over non-targeted approaches.
Evidence: Multiple RCTs (ACT-EARLY, RACAT, ORAL Strategy) demonstrate biologic therapy superiority over csDMARD alone in inadequate responders.""",
     "A"),

    # ── ACS/USPSTF — Preventive ─────────────────────────────────────────
    ("USPSTF-LUNG-2021", "USPSTF", "Lung Cancer Screening with Low-Dose CT",
     2021, "Oncology/Preventive", ["71250"], ["Z12.2"],
     """Grade B Recommendation: Annual screening for lung cancer with low-dose CT (LDCT) is recommended for adults aged 50-80 years who have a 20 pack-year smoking history AND currently smoke or have quit within the past 15 years.
This recommendation updates the 2013 guideline, expanding the eligible population based on evidence from NLST and NELSON trials.
NLST demonstrated 20% reduction in lung cancer mortality and 6.7% reduction in all-cause mortality with annual LDCT screening compared to chest X-ray.
Screening should be discontinued once the person has not smoked for 15 years or develops a health problem that substantially limits life expectancy or the ability to have curative lung surgery.
Evidence Grade: B (moderate certainty that net benefit is moderate).""",
     "B"),
]


def _fetch_uspstf() -> list[tuple]:
    """Pull USPSTF recommendations from their public API."""
    try:
        resp = httpx.get(USPSTF_API, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows = []
        for rec in data:
            gid    = f"USPSTF-{rec.get('id', '')}"
            title  = rec.get('title', '')[:500]
            year   = rec.get('year') or 2020
            topic  = rec.get('topicTitle', '')[:200]
            grade  = rec.get('grade', {}).get('name', '') if isinstance(rec.get('grade'), dict) else str(rec.get('grade', ''))
            text   = rec.get('body', '')
            if not text:
                text = rec.get('summary', '')
            if not text or not title:
                continue
            rows.append((
                gid, "USPSTF", title, int(year), topic,
                [], [],  # no specific CPT/ICD10
                text[:32000], grade[:10], "", text[:32000],
            ))
        print(f"  Fetched {len(rows)} USPSTF recommendations")
        return rows
    except Exception as e:
        print(f"  WARNING: USPSTF API failed ({e}), skipping live fetch")
        return []


def seed():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")

    cur.execute("""
        CREATE OR REPLACE TABLE clinical_guidelines (
            guideline_id        VARCHAR(100)  PRIMARY KEY,
            society             VARCHAR(200),
            guideline_title     VARCHAR(500),
            publication_year    NUMBER(4),
            condition_category  VARCHAR(200),
            cpt_codes           VARCHAR(500),
            icd10_codes         VARCHAR(500),
            recommendation_text TEXT,
            evidence_grade      VARCHAR(10),
            source_url          VARCHAR(1000),
            full_text_chunk     TEXT,
            embedded_at         TIMESTAMP_NTZ
        )
    """)

    # Build rows from hardcoded data
    rows = []
    for gid, society, title, year, category, cpts, icd10s, text, grade in SOCIETY_GUIDELINES:
        rows.append((
            gid, society, title, year, category,
            ",".join(cpts), ",".join(icd10s),
            text, grade, "", text,
        ))

    # Add USPSTF live data
    for r in _fetch_uspstf():
        rows.append((
            r[0], r[1], r[2], r[3], r[4],
            "", "", r[7], r[8], r[9], r[10],
        ))

    ph = ",".join(["%s"] * 11)
    inserted = 0
    for i in range(0, len(rows), 100):
        chunk = rows[i: i + 100]
        vals  = ",".join([f"({ph})"] * len(chunk))
        flat  = [v for row in chunk for v in row]
        cur.execute(
            "INSERT INTO clinical_guidelines "
            "(guideline_id,society,guideline_title,publication_year,condition_category,"
            "cpt_codes,icd10_codes,recommendation_text,evidence_grade,source_url,full_text_chunk) "
            f"VALUES {vals}",
            flat,
        )
        inserted += len(chunk)

    conn.commit()
    conn.close()
    print(f"  Inserted {inserted} clinical guidelines ✓")


if __name__ == "__main__":
    seed()
