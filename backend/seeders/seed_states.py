"""
Seed Snowflake state_regulations table.

Hand-curated data covering:
  - Internal/external appeal deadlines (all 50 states + DC)
  - IRO (Independent Review Organization) contacts
  - Step therapy override laws (36 states as of 2026)
  - AI denial prohibition laws (TX, AZ, MD, CT)
  - Expedited appeal timelines
"""
import sys

sys.path.insert(0, "..")
from services.snowflake_client import get_connection

# fmt: off
STATE_DATA = [
    # (state_code, state_name, internal_days, external_days, iro_name, iro_phone, iro_website,
    #  step_therapy, step_statute, ai_prohibition, ai_statute, expedited_hours)
    ("AL","Alabama",180,45,"Maximus Federal Services","1-888-866-6205","https://www.dol.gov/agencies/ebsa/key-topics/appeals",False,"",False,"",72),
    ("AK","Alaska",180,45,"Maximus Federal Services","1-888-866-6205","https://www.commerce.alaska.gov/web/ins",False,"",False,"",72),
    ("AZ","Arizona",180,45,"Arizona Dept of Insurance","602-364-2499","https://insurance.az.gov",False,"",True,"A.R.S. § 20-3201",72),
    ("AR","Arkansas",180,45,"URAC Accredited IRO","1-800-482-5431","https://www.insurance.arkansas.gov",True,"Ark. Code § 23-99-414",False,"",72),
    ("CA","California",180,30,"DMHC Independent Medical Review","1-888-466-2219","https://www.dmhc.ca.gov",True,"Health & Safety Code § 1367.295",False,"",72),
    ("CO","Colorado",180,45,"Colorado Div of Insurance","303-894-7490","https://doi.colorado.gov",True,"C.R.S. § 10-16-148",False,"",72),
    ("CT","Connecticut",180,45,"CT Insurance Dept","800-203-3447","https://portal.ct.gov/CID",False,"",True,"Conn. Gen. Stat. § 38a-591o",72),
    ("DE","Delaware",180,45,"Delaware Dept of Insurance","302-674-7300","https://insurance.delaware.gov",True,"18 Del. C. § 3372B",False,"",72),
    ("DC","District of Columbia",180,45,"DC Dept of Insurance","202-727-8000","https://disb.dc.gov",True,"D.C. Code § 31-3182",False,"",72),
    ("FL","Florida",365,60,"Florida Dept of Financial Services","1-877-693-5236","https://www.myfloridacfo.com",False,"",False,"",72),
    ("GA","Georgia",180,30,"Georgia Insurance Commissioner","404-656-2056","https://oci.georgia.gov",True,"O.C.G.A. § 33-24-59.17",False,"",72),
    ("HI","Hawaii",180,45,"Hawaii Insurance Division","808-586-2790","https://insurance.ehawaii.gov",False,"",False,"",72),
    ("ID","Idaho",180,45,"Idaho Dept of Insurance","208-334-4250","https://doi.idaho.gov",True,"Idaho Code § 41-392",False,"",72),
    ("IL","Illinois",180,45,"IL Dept of Insurance","217-782-4515","https://insurance.illinois.gov",True,"215 ILCS 5/356z.22",False,"",72),
    ("IN","Indiana",180,45,"Indiana Dept of Insurance","317-232-2385","https://www.in.gov/idoi",True,"Ind. Code § 27-8-29",False,"",72),
    ("IA","Iowa",180,45,"Iowa Insurance Division","515-654-6600","https://iid.iowa.gov",False,"",False,"",72),
    ("KS","Kansas",180,45,"Kansas Insurance Dept","785-296-3071","https://www.ksinsurance.org",True,"K.S.A. § 40-2249d",False,"",72),
    ("KY","Kentucky",180,45,"Kentucky Insurance Dept","502-564-3630","https://insurance.ky.gov",True,"KRS § 304.17A-765",False,"",72),
    ("LA","Louisiana",180,45,"Louisiana Dept of Insurance","225-342-5900","https://www.ldi.la.gov",True,"La. R.S. § 22:1023.4",False,"",72),
    ("ME","Maine",180,45,"Maine Bureau of Insurance","207-624-8475","https://www.maine.gov/pfr/insurance",True,"24-A M.R.S. § 4303-B",False,"",72),
    ("MD","Maryland",180,45,"Maryland Insurance Administration","410-468-2000","https://insurance.maryland.gov",True,"Ins. Art. § 15-158",True,"H.B. 1183 (2024)",72),
    ("MA","Massachusetts",180,45,"MA Office of Consumer Affairs","617-521-7794","https://www.mass.gov/orgs/division-of-insurance",True,"M.G.L. c. 176O § 11A",False,"",72),
    ("MI","Michigan",180,45,"Michigan DIFS","877-999-6442","https://www.michigan.gov/difs",True,"MCL § 500.3406s",False,"",72),
    ("MN","Minnesota",180,45,"Minnesota Commerce Dept","651-296-2488","https://mn.gov/commerce",True,"Minn. Stat. § 62Q.184",False,"",72),
    ("MS","Mississippi",180,45,"Mississippi Insurance Dept","601-359-3569","https://www.mid.ms.gov",False,"",False,"",72),
    ("MO","Missouri",180,45,"Missouri Dept of Insurance","573-751-4126","https://insurance.mo.gov",False,"",False,"",72),
    ("MT","Montana",180,45,"Montana Insurance Commissioner","406-444-2040","https://csimt.gov",True,"Mont. Code § 33-22-706",False,"",72),
    ("NE","Nebraska",180,45,"Nebraska Insurance Dept","402-471-2201","https://doi.nebraska.gov",True,"Neb. Rev. Stat. § 44-5820",False,"",72),
    ("NV","Nevada",180,45,"Nevada Division of Insurance","775-687-0700","https://doi.nv.gov",True,"NRS § 689B.630",False,"",72),
    ("NH","New Hampshire",180,45,"NH Insurance Dept","603-271-2261","https://www.nh.gov/insurance",True,"RSA § 415-J",False,"",72),
    ("NJ","New Jersey",180,45,"NJ Dept of Banking & Insurance","609-292-7272","https://www.state.nj.us/dobi",True,"N.J.S.A. § 26:2S-18.6",False,"",72),
    ("NM","New Mexico",180,45,"NM Office of Superintendent of Insurance","505-827-4601","https://www.osi.state.nm.us",True,"NMSA § 59A-57-10",False,"",72),
    ("NY","New York",180,30,"NY Dept of Financial Services","212-480-6400","https://www.dfs.ny.gov",True,"NY Ins. Law § 4904-a",False,"",72),
    ("NC","North Carolina",180,45,"NC Dept of Insurance","919-807-6750","https://www.ncdoi.gov",True,"N.C.G.S. § 58-51-37.3",False,"",72),
    ("ND","North Dakota",180,45,"ND Insurance Dept","701-328-2440","https://www.nd.gov/ndins",False,"",False,"",72),
    ("OH","Ohio",180,45,"Ohio Dept of Insurance","614-644-2658","https://insurance.ohio.gov",True,"ORC § 3922.16",False,"",72),
    ("OK","Oklahoma",180,45,"Oklahoma Insurance Dept","405-521-2828","https://www.oid.ok.gov",True,"36 O.S. § 6060.16",False,"",72),
    ("OR","Oregon",180,45,"Oregon Insurance Division","503-947-7980","https://dfr.oregon.gov",True,"ORS § 743B.450",False,"",72),
    ("PA","Pennsylvania",180,45,"PA Insurance Dept","717-787-2317","https://www.insurance.pa.gov",True,"40 P.S. § 764j",False,"",72),
    ("RI","Rhode Island",180,45,"RI Insurance Division","401-462-9520","https://dbr.ri.gov/insurance",True,"R.I. Gen. Laws § 27-81-7",False,"",72),
    ("SC","South Carolina",180,45,"SC Dept of Insurance","803-737-6160","https://doi.sc.gov",False,"",False,"",72),
    ("SD","South Dakota",180,45,"SD Division of Insurance","605-773-3563","https://dlr.sd.gov/insurance",False,"",False,"",72),
    ("TN","Tennessee",180,45,"TN Dept of Commerce & Insurance","615-741-2241","https://www.tn.gov/commerce/insurance",True,"Tenn. Code § 56-7-2369",False,"",72),
    ("TX","Texas",180,30,"Texas Dept of Insurance","512-676-6000","https://www.tdi.texas.gov",True,"Tex. Ins. Code § 1369.0546",True,"Tex. Ins. Code § 1274.001",72),
    ("UT","Utah",180,45,"Utah Insurance Dept","801-538-3800","https://insurance.utah.gov",True,"Utah Code § 31A-22-640",False,"",72),
    ("VT","Vermont",180,45,"VT Dept of Financial Regulation","802-828-3301","https://dfr.vermont.gov",True,"8 V.S.A. § 4089i",False,"",72),
    ("VA","Virginia",180,45,"VA Bureau of Insurance","804-371-9741","https://www.scc.virginia.gov/pages/Bureau-of-Insurance",True,"Va. Code § 38.2-3407.15:2",False,"",72),
    ("WA","Washington",180,30,"WA Office of Insurance Commissioner","360-725-7080","https://www.insurance.wa.gov",True,"RCW § 48.43.830",False,"",72),
    ("WV","West Virginia",180,45,"WV Insurance Commission","304-558-3354","https://www.wvinsurance.gov",True,"W.Va. Code § 33-15-4r",False,"",72),
    ("WI","Wisconsin",180,45,"WI Office of Commissioner of Insurance","608-266-3585","https://oci.wi.gov",True,"Wis. Stat. § 632.861",False,"",72),
    ("WY","Wyoming",180,45,"WY Insurance Dept","307-777-7401","https://insurance.wyo.gov",False,"",False,"",72),
]
# fmt: on


def seed():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")

    for row in STATE_DATA:
        (code, name, int_days, ext_days, iro_name, iro_phone, iro_url,
         st_law, st_statute, ai_law, ai_statute, exp_hours) = row
        cur.execute("""
            MERGE INTO state_regulations AS tgt
            USING (SELECT %s AS state_code) AS src ON tgt.state_code = src.state_code
            WHEN NOT MATCHED THEN INSERT (
                state_code, state_name, internal_appeal_deadline_days,
                external_review_deadline_days, iro_name, iro_phone, iro_website,
                step_therapy_override_law, step_therapy_statute,
                ai_denial_prohibition, ai_prohibition_statute,
                expedited_appeal_hours, last_verified
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'2026-03-01')
            WHEN MATCHED THEN UPDATE SET
                step_therapy_override_law = %s,
                ai_denial_prohibition = %s,
                last_verified = '2026-03-01'
        """, (
            code, code, name, int_days, ext_days,
            iro_name, iro_phone, iro_url,
            st_law, st_statute, ai_law, ai_statute, exp_hours,
            st_law, ai_law,
        ))

    conn.commit()
    conn.close()
    print(f"  Seeded {len(STATE_DATA)} state regulations ✓")


if __name__ == "__main__":
    seed()
