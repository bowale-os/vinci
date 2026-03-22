"""
PubMed E-utilities client with write-through Snowflake cache.

Evidence type classification logic:
  Title/abstract keywords → RCT | meta-analysis | systematic_review | cohort | case_series | guideline | other
"""
import hashlib
import re
from datetime import datetime
from typing import Optional

import httpx

from services.snowflake_client import query as sf_query, get_connection

BASE_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL      = "vinci_healthtech"
EMAIL     = "vinci@hackathon.dev"
MAX_RESULTS = 10


def _query_key(cpt_code: str, term: str) -> str:
    return hashlib.sha256(f"{cpt_code}|{term}".encode()).hexdigest()[:32]


def _classify_evidence(title: str, abstract: str) -> str:
    text = (title + " " + abstract).lower()
    if any(k in text for k in ["meta-analysis", "meta analysis", "systematic review", "cochrane"]):
        return "meta-analysis" if "meta-anal" in text else "systematic_review"
    if any(k in text for k in ["randomized controlled", "randomised controlled", "rct", "double-blind", "placebo-controlled"]):
        return "RCT"
    if any(k in text for k in ["cohort study", "retrospective", "prospective study", "observational"]):
        return "cohort"
    if any(k in text for k in ["case series", "case report", "case study"]):
        return "case_series"
    if any(k in text for k in ["guideline", "clinical practice", "consensus statement"]):
        return "guideline"
    return "other"


def _parse_article(article: dict) -> Optional[dict]:
    try:
        medline = article.get("MedlineCitation", {})
        art     = medline.get("Article", {})
        pmid    = str(medline.get("PMID", {}).get("#text", "") or medline.get("PMID", ""))

        title_node = art.get("ArticleTitle", "")
        title = title_node if isinstance(title_node, str) else str(title_node)

        abstract_node = art.get("Abstract", {}).get("AbstractText", "")
        if isinstance(abstract_node, list):
            abstract = " ".join(
                (a.get("#text", "") if isinstance(a, dict) else str(a)) for a in abstract_node
            )
        elif isinstance(abstract_node, dict):
            abstract = abstract_node.get("#text", "")
        else:
            abstract = str(abstract_node) if abstract_node else ""

        journal  = art.get("Journal", {}).get("Title", "")
        pub_date = art.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        year_raw = pub_date.get("Year") or pub_date.get("MedlineDate", "")[:4]
        year     = int(year_raw) if str(year_raw).isdigit() else None

        author_list = art.get("AuthorList", {}).get("Author", [])
        if isinstance(author_list, dict):
            author_list = [author_list]
        authors = []
        for a in author_list[:5]:
            last = a.get("LastName", "")
            fore = a.get("ForeName", "") or a.get("Initials", "")
            if last:
                authors.append(f"{last} {fore}".strip())

        return {
            "pmid": pmid,
            "title": title[:1000],
            "authors": authors,
            "journal": str(journal)[:300],
            "year": year,
            "abstract": abstract[:5000],
            "evidence_type": _classify_evidence(title, abstract),
        }
    except Exception:
        return None


EVIDENCE_RANK = {
    "meta-analysis": 5,
    "systematic_review": 4,
    "RCT": 3,
    "guideline": 3,
    "cohort": 2,
    "case_series": 1,
    "other": 0,
}


async def search_pubmed(cpt_code: str, condition_term: str, force_refresh: bool = False) -> list[dict]:
    """
    Search PubMed for clinical evidence. Returns cached results if available.
    Writes new results back to Snowflake pubmed_cache.
    """
    qkey = _query_key(cpt_code, condition_term)

    if not force_refresh:
        cached = sf_query(
            "SELECT pmid, title, authors, journal, publication_year, abstract_text, evidence_type "
            "FROM pubmed_cache WHERE query_key = %s ORDER BY evidence_type",
            (qkey,),
        )
        if cached:
            return [
                {
                    "pmid": r["PMID"],
                    "title": r["TITLE"],
                    "authors": r["AUTHORS"] or [],
                    "journal": r["JOURNAL"],
                    "year": r["PUBLICATION_YEAR"],
                    "abstract": r["ABSTRACT_TEXT"],
                    "evidence_type": r["EVIDENCE_TYPE"],
                }
                for r in cached
            ]

    # Build query: CPT description + condition + clinical terms
    query_str = f'("{condition_term}"[Title/Abstract] OR "{cpt_code}"[Title/Abstract]) AND (clinical trial[pt] OR systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt])'

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: esearch
        search_resp = await client.get(f"{BASE_URL}/esearch.fcgi", params={
            "db": "pubmed", "term": query_str, "retmax": MAX_RESULTS,
            "retmode": "json", "sort": "relevance", "tool": TOOL, "email": EMAIL,
        })
        pmids = search_resp.json().get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []

        # Step 2: efetch XML → parse
        fetch_resp = await client.get(f"{BASE_URL}/efetch.fcgi", params={
            "db": "pubmed", "id": ",".join(pmids), "retmode": "xml",
            "tool": TOOL, "email": EMAIL,
        })

        import xmltodict
        data = xmltodict.parse(fetch_resp.text)
        articles_raw = data.get("PubmedArticleSet", {}).get("PubmedArticle", [])
        if isinstance(articles_raw, dict):
            articles_raw = [articles_raw]

    articles = [a for raw in articles_raw if (a := _parse_article(raw))]

    # Sort by evidence rank
    articles.sort(key=lambda a: EVIDENCE_RANK.get(a["evidence_type"], 0), reverse=True)

    # Write to cache
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("USE DATABASE vinci_db")
    cur.execute("USE SCHEMA insurer_policies")
    for art in articles:
        cur.execute("""
            MERGE INTO pubmed_cache AS tgt
            USING (SELECT %s AS pmid, %s AS query_key) AS src
              ON tgt.pmid = src.pmid AND tgt.query_key = src.query_key
            WHEN NOT MATCHED THEN INSERT (
                query_key, cpt_code, condition_term, pmid, title, authors,
                journal, publication_year, abstract_text, evidence_type
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            art["pmid"], qkey,
            qkey, cpt_code, condition_term, art["pmid"], art["title"],
            art["authors"], art["journal"], art["year"],
            art["abstract"], art["evidence_type"],
        ))
    conn.commit()
    conn.close()

    return articles
