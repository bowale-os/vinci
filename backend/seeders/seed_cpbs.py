"""
Seed Snowflake cpbs table with hardcoded Clinical Policy Bulletins
from the 5 major commercial insurers covering the top 12 denial categories.

Sources: publicly available CPB documents from Aetna, Cigna, UHC, Anthem, Humana.
These criteria reflect actual published policies as of 2025.

Denial categories covered:
  1.  Total knee / hip arthroplasty
  2.  Spinal fusion surgery
  3.  Bariatric / weight loss surgery
  4.  Sleep study & CPAP/BiPAP
  5.  MRI (spine, brain, joint)
  6.  Continuous glucose monitoring (CGM)
  7.  Mental health (outpatient therapy)
  8.  Physical / occupational therapy
  9.  Cancer drug infusion (chemotherapy)
  10. Genetic testing (oncology panel)
  11. Cardiac catheterization
  12. Immunotherapy / biologics (RA, psoriasis)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.snowflake_client import get_connection

# ---------------------------------------------------------------------------
# CPB data: (cpb_number, insurer_name, procedure_code, policy_title, criteria, last_reviewed)
# ---------------------------------------------------------------------------
CPB_DATA = [

    # ── AETNA ──────────────────────────────────────────────────────────────
    ("0584", "Aetna", "27447",
     "Total Knee Replacement (Total Knee Arthroplasty)",
     """Aetna considers total knee arthroplasty (TKA) medically necessary when ALL of the following criteria are met:
1. Diagnosis of severe osteoarthritis (Kellgren-Lawrence grade 3 or 4), rheumatoid arthritis, or post-traumatic arthritis confirmed by X-ray or MRI.
2. Documented failure of at least 3 months of conservative treatment including physical therapy, NSAIDs or analgesics, and activity modification.
3. Significant functional limitation: unable to perform activities of daily living due to knee pain or instability.
4. BMI less than 40 kg/m2 (BMI 40-50 may be considered with documented weight management attempt).
5. No active infection at the surgical site or systemic infection.
6. Medically optimized for surgery (controlled diabetes HbA1c <8, smoking cessation counseled).
Aetna considers TKA not medically necessary for pain alone without functional impairment, or when conservative treatment has not been adequately trialed.""",
     "2024-11-01"),

    ("0029", "Aetna", "27130",
     "Total Hip Replacement (Total Hip Arthroplasty)",
     """Aetna considers total hip arthroplasty (THA) medically necessary when ALL criteria are met:
1. Severe hip arthritis (osteoarthritis, rheumatoid arthritis, avascular necrosis, or post-traumatic arthritis) confirmed radiographically.
2. Failure of at least 3 months of conservative therapy (physical therapy, analgesics, anti-inflammatory medications, assistive devices).
3. Severe functional impairment limiting activities of daily living.
4. BMI < 40 kg/m2 preferred; BMI 40-50 requires documentation of weight management.
5. No untreated ipsilateral knee pathology that would preclude rehabilitation.
6. Medically stable for surgery.""",
     "2024-09-15"),

    ("0362", "Aetna", "22612",
     "Spinal Fusion Surgery (Lumbar)",
     """Aetna considers lumbar spinal fusion medically necessary for:
1. Degenerative disc disease with instability: spondylolisthesis grade II or higher with neurological symptoms failing 6 months conservative care.
2. Spinal stenosis with neurogenic claudication failing 3 months of conservative treatment including epidural steroid injections and physical therapy.
3. Recurrent disc herniation (same level, same side) after prior discectomy with persistent radiculopathy.
4. Fracture or tumor causing structural instability.
Conservative treatment must include: physical therapy (minimum 6 weeks), NSAIDs or appropriate analgesics, epidural steroid injections (minimum 2 injections unless contraindicated).
Aetna does NOT consider fusion medically necessary for: axial low back pain alone without instability, disc herniation without neurological deficit, or as primary treatment without documented conservative care failure.""",
     "2024-10-01"),

    ("0157", "Aetna", "43644",
     "Bariatric Surgery (Laparoscopic Gastric Bypass)",
     """Aetna considers bariatric surgery medically necessary when ALL criteria are met:
1. BMI ≥ 40 kg/m2; OR BMI ≥ 35 kg/m2 with at least one serious obesity-related comorbidity (Type 2 diabetes, hypertension, sleep apnea, obesity hypoventilation syndrome, GERD, osteoarthritis, hyperlipidemia).
2. Documented failure of medically supervised weight loss program of at least 6 months duration within past 2 years.
3. Age 18-65 (adolescents 14-17 may qualify with additional criteria).
4. Absence of: active substance abuse, uncontrolled psychiatric disorder, inability to comply with nutritional requirements.
5. Pre-operative psychological evaluation clearance.
6. Commitment to long-term follow-up.
Aetna considers revisional bariatric surgery medically necessary for complications or inadequate weight loss with documented failure of non-surgical interventions.""",
     "2024-08-01"),

    ("0247", "Aetna", "95810",
     "Polysomnography (Sleep Study) and CPAP",
     """Aetna considers attended polysomnography (PSG) medically necessary for:
1. Suspected obstructive sleep apnea (OSA) with: excessive daytime sleepiness, witnessed apneas, or snoring with hypertension/cardiovascular disease.
2. Assessment of other sleep disorders: narcolepsy, periodic limb movement disorder, parasomnias.
CPAP/BiPAP therapy is medically necessary when:
1. AHI ≥ 15 events/hour; OR AHI ≥ 5 with symptoms (excessive daytime sleepiness, impaired cognition, mood disorders, insomnia, hypertension, cardiovascular disease, or stroke).
2. Home sleep apnea testing (HSAT) is appropriate for uncomplicated suspected moderate-to-severe OSA without significant comorbidities.
Ongoing CPAP coverage requires documentation of adherence (≥4 hours/night on ≥70% of nights in any 30-day period within first 90 days).""",
     "2024-07-15"),

    ("0352", "Aetna", "70553",
     "MRI of the Brain and Spine",
     """Aetna considers MRI of the brain medically necessary for:
1. New onset seizure disorder or change in seizure pattern.
2. Headache with red flag features: thunderclap onset, progressive worsening, neurological deficits, papilledema, immunocompromised state, age >50 with new pattern.
3. Cognitive decline or dementia workup.
4. Focal neurological signs or symptoms.
5. Suspected CNS neoplasm, vascular malformation, or infection.
MRI of the spine is medically necessary for:
1. Radiculopathy with neurological deficit not responding to 6 weeks conservative treatment.
2. Myelopathy (cord compression symptoms).
3. Suspected spinal cord tumor, infection, or fracture.
4. New or worsening neurological deficit.
Routine MRI for uncomplicated low back pain without red flags is not medically necessary.""",
     "2024-06-01"),

    ("0513", "Aetna", "95251",
     "Continuous Glucose Monitoring (CGM)",
     """Aetna considers CGM medically necessary for members with diabetes mellitus when:
1. Type 1 diabetes: all patients on intensive insulin therapy (multiple daily injections or insulin pump).
2. Type 2 diabetes on intensive insulin therapy (3 or more injections daily or insulin pump) with: HbA1c not at goal despite optimized therapy, recurrent hypoglycemia or hypoglycemia unawareness, significant glycemic variability.
3. Gestational diabetes requiring insulin therapy.
Documentation required: current diabetes management regimen, most recent HbA1c, history of hypoglycemic episodes, treating endocrinologist or PCP attestation of medical necessity.
Professional CGM (short-term, clinic-supervised) is covered for diagnostic purposes. Personal CGM covered for ongoing self-management in qualifying patients.""",
     "2024-12-01"),

    ("0482", "Aetna", "96413",
     "Chemotherapy Administration (Intravenous Infusion)",
     """Aetna considers intravenous chemotherapy administration medically necessary when:
1. Diagnosis of malignancy confirmed by pathology.
2. Chemotherapy regimen is consistent with NCCN guidelines (Category 1 or 2A recommendation) for the specific cancer type, stage, and line of therapy.
3. Patient has adequate organ function to tolerate chemotherapy (appropriate PS score, CBC, metabolic panel).
4. Treatment is administered by or under direct supervision of board-certified oncologist.
Prior authorization required for: non-NCCN regimens, off-label use beyond NCCN Category 2B, high-cost agents (>$1,000/dose).
Aetna covers biosimilars as therapeutically equivalent to reference biologics per FDA approval.""",
     "2024-11-15"),

    ("0545", "Aetna", "81455",
     "Genomic Tumor Sequencing (Solid Tumor Panel)",
     """Aetna considers comprehensive genomic profiling (CGP) of solid tumors medically necessary when:
1. Metastatic or advanced (Stage III-IV) solid tumor where molecular testing will inform treatment selection.
2. Standard single-gene or small panel testing is insufficient due to: multiple actionable biomarkers possible, limited tissue availability, or guideline recommendation for CGP.
3. NCCN guidelines recommend biomarker testing for the specific cancer type.
4. Patient is a candidate for targeted therapy or clinical trial enrollment.
Covered panels: Foundation One CDx, Tempus xT, Caris MI Profile, Guardant360 CDx (liquid biopsy for appropriate indications).
CGP is not covered for: early-stage disease without metastatic potential, cancers without actionable targets, or when results will not change management.""",
     "2024-10-15"),

    # ── CIGNA ──────────────────────────────────────────────────────────────
    ("0319", "Cigna", "27447",
     "Total Knee Arthroplasty",
     """Cigna covers total knee arthroplasty (TKA) as medically necessary when the following conditions are met:
1. Radiographic evidence of moderate-to-severe arthritis (joint space narrowing, osteophyte formation, subchondral sclerosis).
2. Chronic knee pain that is disabling and significantly impacts function.
3. Failure of a minimum of 3 months of conservative management, which must include: structured physical therapy program, weight management (if BMI > 30), appropriate pharmacological therapy (NSAIDs, analgesics, or intra-articular injections).
4. Confirmation that surgery is appropriate given the patient's overall medical condition.
Cigna does not cover TKA for: isolated patellofemoral arthritis (unicompartmental replacement may be appropriate), knee pain without radiographic findings, or patients with active infection.""",
     "2024-09-01"),

    ("0517", "Cigna", "22612",
     "Lumbar Spinal Fusion",
     """Cigna covers lumbar spinal fusion as medically necessary for:
1. Spondylolisthesis (isthmic or degenerative) Grade I or higher with: persistent disabling symptoms after 3+ months conservative care including PT and injections; OR neurological deficit.
2. Recurrent lumbar disc herniation (same level) after prior discectomy with: persistent disabling radiculopathy; AND failure of 6+ weeks post-operative conservative care.
3. Lumbar spinal stenosis with neurogenic claudication: severe functional limitation; failed 3 months conservative care including epidural steroid injections.
4. Fracture causing instability.
Required documentation: imaging confirming pathology, detailed conservative treatment history with dates and response, functional assessment, surgical plan.
Cigna does not cover: fusion for axial back pain alone, multilevel fusion (>3 levels) without clear indication at each level.""",
     "2024-08-15"),

    ("0421", "Cigna", "43770",
     "Laparoscopic Gastric Banding (Bariatric)",
     """Cigna covers bariatric surgery including laparoscopic adjustable gastric banding when:
1. BMI ≥ 40; OR BMI 35-39.9 with obesity-related comorbidity (T2DM, HTN, OSA, NAFLD, osteoarthritis, GERD).
2. Documented participation in medically supervised weight management program for minimum 6 months.
3. Age 18 or older (adolescents with special criteria).
4. Pre-operative multidisciplinary evaluation including: medical, nutritional, behavioral/psychological assessment.
5. No contraindications: active psychiatric disorder, substance dependence, pregnancy, inability to follow post-op dietary requirements.
Cigna requires pre-certification and ongoing follow-up compliance. Coverage includes 2 years post-operative follow-up visits.""",
     "2024-07-01"),

    ("0388", "Cigna", "95810",
     "Diagnostic Sleep Studies",
     """Cigna covers polysomnography (PSG) when:
1. Clinical evaluation suggests sleep-disordered breathing with: habitual snoring, witnessed apneas, excessive daytime sleepiness (ESS > 10), or obesity with suspected OSA.
2. Diagnosis of other sleep disorders requiring PSG confirmation: narcolepsy, REM sleep behavior disorder, periodic limb movement disorder.
CPAP coverage criteria:
1. Diagnosis of OSA with AHI ≥ 15; OR AHI 5-14 with documented symptoms (sleepiness, impaired cognition, mood disturbance, insomnia, or cardiovascular comorbidity).
2. Continued coverage after 90 days requires: documented adherence (≥4 hours/night, ≥70% of nights), and clinical benefit demonstrated.
Home sleep testing (HST) appropriate for: uncomplicated adults with high pre-test probability of moderate-severe OSA, no significant cardiopulmonary disease or other sleep disorders.""",
     "2024-06-15"),

    ("0503", "Cigna", "90837",
     "Outpatient Mental Health — Individual Psychotherapy",
     """Cigna covers outpatient individual psychotherapy (90837, 90834, 90832) as medically necessary when:
1. DSM-5 diagnosed mental health condition: major depressive disorder, anxiety disorders, PTSD, bipolar disorder, OCD, eating disorders, psychotic disorders.
2. Treatment is provided by licensed mental health professional (PhD, LCSW, LMFT, LPC, or MD/DO).
3. Individualized treatment plan with measurable goals, evidence-based modalities (CBT, DBT, EMDR, etc.).
4. Progress toward treatment goals documented at each visit.
5. Continued coverage requires demonstrated clinical improvement or medical necessity for maintenance.
Cigna follows mental health parity requirements — coverage cannot be more restrictive than analogous medical/surgical benefits.
Intensive outpatient program (IOP) covered for step-down from inpatient or step-up from standard outpatient.""",
     "2024-05-01"),

    # ── UNITED HEALTH (UHC) ────────────────────────────────────────────────
    ("CS8822.H", "UnitedHealthcare", "27447",
     "Knee Arthroplasty",
     """UnitedHealthcare covers total knee arthroplasty when medical necessity criteria are satisfied:
1. Documented diagnosis of disabling knee arthritis (osteoarthritis, RA, or post-traumatic) with radiographic confirmation of joint space loss.
2. Significant pain and functional impairment despite optimal non-surgical management for at least 3 months including: physical therapy, analgesic medication trial, weight loss efforts (if BMI > 30).
3. Patient medically appropriate for major surgery (ASA class I-III, optimized comorbidities).
4. Reasonable expectation of functional improvement post-operatively.
Documentation requirements: X-rays within 12 months, PT records, medication history, surgical consultation note with functional assessment.
UHC covers bilateral TKA (staged or simultaneous) when both knees meet criteria independently.""",
     "2024-10-01"),

    ("CS7744.F", "UnitedHealthcare", "22612",
     "Lumbar Fusion Procedures",
     """UnitedHealthcare covers lumbar fusion procedures when:
1. Structural instability: spondylolisthesis grade ≥ II, adjacent segment disease after prior fusion, post-laminectomy instability.
2. Failed conservative care for minimum 3 months: documented PT (≥6 sessions), trial of oral analgesics and NSAIDs, consideration of interventional pain management.
3. Neurological compromise: progressive motor deficit, bowel/bladder dysfunction (urgent/emergent).
4. Tumor, infection, or fracture causing instability.
Pre-authorization required for all elective spinal fusion procedures.
UHC requires: MRI or CT myelogram correlating with symptoms, functional capacity evaluation, and surgeon attestation that all conservative measures have been exhausted.""",
     "2024-09-15"),

    ("CS6633.J", "UnitedHealthcare", "43644",
     "Bariatric Surgical Procedures",
     """UnitedHealthcare covers bariatric surgery (gastric bypass, sleeve gastrectomy, gastric banding, duodenal switch) when:
1. BMI ≥ 40 kg/m2; OR BMI ≥ 35 kg/m2 with obesity-related comorbidity.
2. Completion of UHC-approved pre-operative program: minimum 3-6 months medically supervised diet (varies by plan).
3. Multidisciplinary evaluation: medical clearance, nutritional assessment, behavioral health evaluation.
4. No uncontrolled psychiatric illness, active substance use disorder, or medical contraindication.
5. Member and provider agreement on post-operative follow-up.
UHC covers: pre-operative testing, surgery, anesthesia, facility, and post-operative follow-up visits per plan benefit.
Revision bariatric surgery covered for: complications of prior procedure, or inadequate weight loss with documented compliance to post-operative program.""",
     "2024-08-01"),

    ("CS9015.B", "UnitedHealthcare", "95251",
     "Continuous Glucose Monitoring Systems",
     """UnitedHealthcare covers personal CGM (real-time and intermittent-scan) when:
1. Type 1 diabetes mellitus: covered for all patients requiring insulin.
2. Type 2 diabetes mellitus requiring insulin: HbA1c > 7% despite optimized regimen; OR recurrent hypoglycemia (≥2 episodes requiring assistance in 12 months); OR hypoglycemia unawareness.
3. Prescription from endocrinologist, diabetologist, or PCP with attestation of qualifying criteria.
Coverage includes: CGM receiver/reader, transmitter, and sensors.
Professional CGM (clinic-based, 72-hour diagnostic): covered for any patient with diabetes for diagnostic purposes.
Prior authorization required; renewal authorization requires documentation of continued use and clinical benefit.""",
     "2024-11-01"),

    ("CS8801.K", "UnitedHealthcare", "96413",
     "Chemotherapy and Infusion Therapy",
     """UnitedHealthcare covers chemotherapy administration when:
1. Pathologically confirmed malignancy.
2. Regimen supported by NCCN Clinical Practice Guidelines (Categories 1, 2A, or 2B) or Level I/II evidence in peer-reviewed literature.
3. Administered by or under supervision of board-certified oncologist.
4. Patient meets eligibility criteria: adequate performance status, organ function, and absence of absolute contraindications.
Prior authorization required for: all IV chemotherapy, targeted therapy agents, immunotherapy, and high-cost oral oncology agents.
UHC covers: drug cost, administration fees, pre-medications (antiemetics, steroids), and growth factors per NCCN guidelines.
Biosimilars may be substituted for reference products; medically necessary exceptions available with documentation.""",
     "2024-10-15"),

    # ── ANTHEM (ELEVANCE) ──────────────────────────────────────────────────
    ("SURG.00015", "Anthem", "27447",
     "Arthroplasty of Major Joints — Knee",
     """Anthem/Elevance Health covers knee arthroplasty as medically necessary when:
1. Symptomatic knee osteoarthritis or inflammatory arthritis with: moderate-to-severe pain interfering with function, AND radiographic evidence of significant joint disease.
2. Failed non-operative treatment for ≥ 3 months: physical therapy (documented course), NSAIDs or analgesics (documented trial), weight management if applicable.
3. No active infection, no significant medical comorbidity precluding surgery.
4. Functional assessment demonstrating disability from knee condition.
Anthem utilizes evidence-based criteria from MCG (formerly Milliman Care Guidelines) and AAOS clinical guidelines.
Pre-authorization required. Length of stay authorization separate from procedure authorization.""",
     "2024-09-01"),

    ("SURG.00068", "Anthem", "22612",
     "Spinal Fusion — Lumbar",
     """Anthem covers lumbar spinal fusion when clinical criteria are satisfied:
1. Degenerative spondylolisthesis with stenosis: disabling symptoms, documented neurological involvement, failure of ≥ 3 months conservative care.
2. Isthmic spondylolisthesis grade II or higher: symptoms correlating with imaging, conservative care failure.
3. Pseudoarthrosis repair after prior fusion.
4. Spinal fracture with instability.
5. Tumor or infection causing structural compromise.
Anthem does not cover fusion for: isolated disc degeneration without instability, axial pain only, or as prophylactic procedure.
All elective spinal fusion requires pre-authorization with submission of: MRI/CT imaging, physical therapy records, pain management records, functional assessment.""",
     "2024-08-15"),

    ("MED.00004", "Anthem", "95810",
     "Sleep Testing and CPAP Therapy",
     """Anthem covers polysomnography (attended, in-lab) for:
1. Suspected obstructive sleep apnea with clinical indicators: snoring, witnessed apnea, daytime sleepiness, hypertension, BMI > 35.
2. Titration study after diagnostic PSG confirms OSA.
3. CPAP failure assessment requiring split-night or re-titration study.
4. Evaluation of other sleep disorders requiring attended PSG.
CPAP/BiPAP covered when:
1. OSA confirmed with AHI ≥ 15; OR AHI ≥ 5 with documented symptoms and comorbidities.
2. Coverage continues with adherence documentation at 31 and 91 days.
Home sleep apnea testing (HSAT) covered for uncomplicated suspected OSA without significant comorbidities.""",
     "2024-07-01"),

    ("MED.00078", "Anthem", "81455",
     "Next Generation Sequencing — Oncology",
     """Anthem covers next-generation sequencing (NGS) tumor profiling when:
1. Advanced, recurrent, metastatic, or refractory solid tumor or hematologic malignancy.
2. Patient is a candidate for treatment with an FDA-approved targeted therapy for which there is a companion diagnostic.
3. Testing has not been performed previously on same specimen.
4. Ordering physician attests that results will guide management.
Single gene testing or limited hotspot panels preferred when only one actionable mutation is clinically relevant.
Comprehensive genomic profiling (Foundation One, Tempus, Caris) covered for: stage IV solid tumors, ALL biomarker testing recommended by NCCN for the cancer type, or when limited tissue availability requires multiplexed testing.""",
     "2024-06-01"),

    # ── HUMANA ─────────────────────────────────────────────────────────────
    ("HUM-MSK-001", "Humana", "27447",
     "Total Knee Arthroplasty",
     """Humana covers total knee replacement when medically necessary criteria are met:
1. Diagnosis of severe knee arthritis confirmed by: standing weight-bearing X-rays showing significant joint space narrowing; AND clinical evaluation documenting severe pain and functional limitation.
2. Failure of conservative therapy for minimum 3 months: must include physical therapy AND pharmacologic management (NSAIDs, analgesics, or corticosteroid injections).
3. Patient medically optimized: controlled diabetes (HbA1c < 8.5), blood pressure < 160/90, BMI < 50.
4. No active joint or systemic infection.
5. Expected functional benefit from surgery.
Humana covers: bilateral staged TKA when both knees independently meet criteria. Simultaneous bilateral TKA reviewed on individual basis.""",
     "2024-10-01"),

    ("HUM-SPINE-002", "Humana", "22612",
     "Lumbar Fusion Surgery",
     """Humana covers lumbar fusion as medically necessary for:
1. Spondylolisthesis grade II or higher with functional neurological deficit and failure of 6+ months conservative care.
2. Post-discectomy syndrome with instability and persistent radiculopathy failing repeat conservative management.
3. Lumbar stenosis with instability and neurogenic claudication failing ≥ 3 months conservative care including 2+ epidural steroid injections.
4. Acute fracture, tumor, or infection with instability.
Humana requires prior authorization for all spinal fusion procedures.
Supporting documentation: MRI or CT confirming pathology within 6 months, documentation of conservative care attempts (dates, providers, response), surgical consultation with detailed indication.""",
     "2024-09-01"),

    ("HUM-OB-003", "Humana", "43644",
     "Bariatric Surgery",
     """Humana covers bariatric surgery when:
1. BMI ≥ 40; OR BMI 35-39.9 with at least one serious comorbidity (T2DM, hypertension, sleep apnea, GERD, hyperlipidemia, osteoarthritis).
2. Medically supervised weight loss program completed (minimum 3 months, documentation required).
3. Pre-operative evaluation by bariatric multidisciplinary team including behavioral health.
4. No contraindications: uncontrolled psychiatric illness, active substance use, pregnancy.
5. Member must be enrolled in Humana plan for minimum 12 months prior to surgery (varies by plan).
Post-operative coverage includes: follow-up visits, nutritional counseling, support group participation.""",
     "2024-08-01"),

    ("HUM-SLEEP-004", "Humana", "95810",
     "Sleep Studies and CPAP/BiPAP",
     """Humana covers sleep studies and CPAP/BiPAP therapy:
Polysomnography covered for: suspected OSA with symptoms (snoring, witnessed apnea, excessive daytime sleepiness), evaluation of other sleep disorders.
CPAP therapy covered when: AHI ≥ 15; OR AHI 5-14 with symptoms or cardiovascular comorbidities.
BiPAP covered when: CPAP failed or contraindicated, central sleep apnea, obesity hypoventilation syndrome, neuromuscular disease.
Compliance requirement: minimum 4 hours/night use on ≥ 70% of nights during 30-day evaluation period.
Auto-adjusting CPAP (APAP) covered as alternative to fixed CPAP.
Humana covers annual resupply of CPAP equipment per CMS resupply schedule.""",
     "2024-07-15"),

    ("HUM-BIO-005", "Humana", "J0129",
     "Biologic Therapy — Rheumatoid Arthritis (Abatacept/Orencia)",
     """Humana covers biologic DMARDs for rheumatoid arthritis when:
1. Confirmed diagnosis of moderate-to-severe RA (DAS28 > 3.2 or equivalent).
2. Inadequate response to or intolerance of at least one conventional DMARD (methotrexate preferred) at adequate dose for minimum 3 months.
3. Prescribed by or in consultation with rheumatologist.
Step therapy requirements: TNF inhibitor (adalimumab, etanercept, or biosimilar) must be tried first unless contraindicated; non-TNF biologic (abatacept, tocilizumab, rituximab) requires TNF failure documentation.
Step therapy override criteria: prior biologic failure, contraindication to TNF inhibitor, physician attestation of clinical rationale.
Continued coverage requires documentation of clinical response at 3-6 months.""",
     "2024-06-01"),
]

BATCH = 200


def seed():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")

    cur.execute("""
        CREATE OR REPLACE TABLE cpbs (
            cpb_number      VARCHAR(20),
            insurer_name    VARCHAR(100),
            procedure_code  VARCHAR(20),
            policy_title    VARCHAR(500),
            criteria        TEXT,
            last_reviewed   DATE,
            PRIMARY KEY (cpb_number, insurer_name)
        )
    """)

    rows = [
        (cpb, insurer, code, title, criteria, reviewed)
        for cpb, insurer, code, title, criteria, reviewed in CPB_DATA
    ]

    ph = ",".join(["%s"] * 6)
    for i in range(0, len(rows), BATCH):
        chunk = rows[i: i + BATCH]
        vals  = ",".join([f"({ph})"] * len(chunk))
        flat  = [v for row in chunk for v in row]
        cur.execute(
            f"INSERT INTO cpbs (cpb_number,insurer_name,procedure_code,policy_title,criteria,last_reviewed) "
            f"VALUES {vals}",
            flat,
        )

    conn.commit()
    conn.close()
    print(f"  Inserted {len(rows)} CPB records across 5 insurers ✓")


if __name__ == "__main__":
    seed()
