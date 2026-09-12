# ==========================================================
# TENDERWISE AI
# Module: Requirement Matching, Risk Analysis, Bid Decision,
#         AI Report Generation, and Submission Checklist
#
# Author: Muteeba
# Description: Takes structured tender requirements and company
# capabilities (produced by the PDF Processing + Analysis stage)
# and produces a complete bid-readiness assessment.
# ==========================================================

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from the .env file")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "openai/gpt-oss-120b"


def ask_llm(prompt, system_prompt=(
    "You are a helpful tender analysis assistant. "
    "Always respond ONLY in valid JSON, with no extra text and no markdown backticks."
)):
    """Send a prompt to the LLM and return the raw text response."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


# ---------------- Sample Data (for standalone testing only) ----------------

SAMPLE_INPUT = {
    "tender_title": "Construction of Highway Section A",
    "deadline": "2026-10-15",
    "category": "Construction",
    "requirements": [
        {
            "requirement": "Minimum 5 years construction experience",
            "category": "Experience",
            "priority": "Mandatory",
            "evidence": {"page": 12, "text": "Bidder must have at least 5 years of relevant construction experience."}
        },
        {
            "requirement": "ISO 9001 certification required",
            "category": "Certification",
            "priority": "Mandatory",
            "evidence": {"page": 15, "text": "Bidders must hold a valid ISO 9001 certification."}
        },
        {
            "requirement": "Minimum annual turnover of 50 million PKR",
            "category": "Financial",
            "priority": "Mandatory",
            "evidence": {"page": 20, "text": "Minimum annual turnover of PKR 50 million required."}
        },
        {
            "requirement": "Submission of company registration certificate",
            "category": "Documents",
            "priority": "Mandatory",
            "evidence": {"page": 25, "text": "Company registration certificate must be submitted."}
        },
        {
            "requirement": "Experience in highway projects specifically",
            "category": "Experience",
            "priority": "Preferred",
            "evidence": {"page": 13, "text": "Preference will be given to bidders with highway-specific experience."}
        }
    ],
    "company_info": {
        "name": "ABC Construction Pvt Ltd",
        "services": ["Road construction", "Bridge building"],
        "experience": "7 years in highway construction",
        "certifications": ["ISO 9001"],
        "projects": ["Highway Project X", "Bridge Y"],
        "financial_info": {"annual_turnover": "60 million PKR"},
        "registrations": ["SECP Registered"]
    }
}


# ---------------- Adapter for the Analysis stage's real output ----------------
# The upstream PDF Processing + Analysis module returns output in this shape:
# {
#   "tender_analysis": {tender_title, tender_category, deadline, requirements: [...]},
#   "company_analysis": {company_name, services, experience, certifications,
#                         projects, technical_capabilities, financial_information,
#                         registrations, relevant_expertise}
# }
# This function converts that real output into the flat structure this
# module's functions expect.

def adapt_analysis_output(real_output):
    tender = real_output["tender_analysis"]
    company = real_output["company_analysis"]

    return {
        "tender_title": tender.get("tender_title", "Not specified"),
        "deadline": tender.get("deadline", "Not specified"),
        "category": tender.get("tender_category", "Not specified"),
        "requirements": tender.get("requirements", []),
        "company_info": {
            "name": company.get("company_name", "Not specified"),
            "services": company.get("services", []),
            "experience": company.get("experience", []),
            "certifications": company.get("certifications", []),
            "projects": company.get("projects", []),
            "technical_capabilities": company.get("technical_capabilities", []),
            "financial_info": company.get("financial_information", []),
            "registrations": company.get("registrations", []),
            "relevant_expertise": company.get("relevant_expertise", [])
        }
    }


# ---------------- Requirement Matching ----------------

def match_requirement(requirement, company_info):
    """Compare a single requirement against the company profile."""
    prompt = f"""
Compare this tender requirement with the company profile and classify it.

REQUIREMENT:
{requirement}

COMPANY PROFILE:
{company_info}

Return ONLY this JSON structure:
{{
  "requirement": "the requirement text",
  "category": "the category",
  "priority": "the priority",
  "status": "Matched" or "Missing" or "Unclear",
  "company_evidence": "relevant proof from the company profile, or 'None found'",
  "reason": "a short explanation of why this status was chosen"
}}
"""
    result = ask_llm(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {
            "requirement": requirement.get("requirement"),
            "status": "Unclear",
            "reason": "Could not parse the AI response",
            "company_evidence": "N/A",
            "category": requirement.get("category"),
            "priority": requirement.get("priority")
        }


def match_all_requirements(analysis_output):
    """Run matching for every requirement in the tender."""
    results = []
    for req in analysis_output["requirements"]:
        matched = match_requirement(req, analysis_output["company_info"])
        results.append(matched)
    return results


# ---------------- Compliance Calculation ----------------

def calculate_compliance(matched_results):
    """Calculate compliance totals and percentage from matching results."""
    total = len(matched_results)
    matched = sum(1 for r in matched_results if r["status"] == "Matched")
    missing = sum(1 for r in matched_results if r["status"] == "Missing")
    unclear = sum(1 for r in matched_results if r["status"] == "Unclear")
    percentage = round((matched / total) * 100, 2) if total > 0 else 0

    return {
        "total_requirements": total,
        "matched": matched,
        "missing": missing,
        "unclear": unclear,
        "compliance_percentage": percentage
    }


# ---------------- Risk Analysis ----------------

def analyze_risks(matched_results, tender_title):
    """Identify high, medium, and low risks based on the matching results."""
    prompt = f"""
Based on the following requirement matching results for the tender "{tender_title}",
identify risks the company faces if they bid on this tender.

MATCHING RESULTS:
{matched_results}

Return ONLY this JSON structure:
{{
  "high_risks": [{{"risk": "...", "impact": "...", "reason": "..."}}],
  "medium_risks": [{{"risk": "...", "impact": "...", "reason": "..."}}],
  "low_risks": [{{"risk": "...", "impact": "...", "reason": "..."}}]
}}

Focus especially on Missing or Unclear Mandatory requirements as high risks.
"""
    result = ask_llm(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {
            "high_risks": [],
            "medium_risks": [],
            "low_risks": [],
            "error": "Could not parse the AI response"
        }


# ---------------- Bid Decision ----------------
# The decision is determined by fixed business rules first (for
# reliability and consistency), and the LLM is only used to write a
# clear, well-explained reason for that decision.

def bid_decision(matched_results, compliance, risks):
    mandatory_missing = sum(
        1 for r in matched_results
        if r.get("status") == "Missing" and r.get("priority") == "Mandatory"
    )
    mandatory_unclear = sum(
        1 for r in matched_results
        if r.get("status") == "Unclear" and r.get("priority") == "Mandatory"
    )
    high_risk_count = len(risks.get("high_risks", []))
    compliance_pct = compliance.get("compliance_percentage", 0)

    if mandatory_missing > 0:
        forced_decision = "NO-BID"
        forced_reason_hint = f"{mandatory_missing} mandatory requirement(s) are missing."
    elif mandatory_unclear > 0 or high_risk_count > 0:
        forced_decision = "CONDITIONAL BID"
        forced_reason_hint = "There are unclear mandatory requirements or high risks that need resolving."
    elif compliance_pct >= 80:
        forced_decision = "BID"
        forced_reason_hint = "Compliance is high and no critical issues were found."
    else:
        forced_decision = "CONDITIONAL BID"
        forced_reason_hint = "Compliance is moderate; some gaps should be addressed."

    prompt = f"""
The correct bid decision has already been determined by business rules as: {forced_decision}
Reason hint: {forced_reason_hint}

Based on the compliance data and risk analysis below, write a clear, well-explained
reason for this decision. Do NOT change the decision itself, only explain it clearly.

COMPLIANCE:
{compliance}

RISKS:
{risks}

Return ONLY this JSON structure:
{{
  "decision": "{forced_decision}",
  "reason": "a clear explanation combining the compliance percentage and risk levels"
}}
"""
    result = ask_llm(prompt)
    try:
        parsed = json.loads(result)
        parsed["decision"] = forced_decision  # the rule-based decision is always final
        return parsed
    except Exception:
        return {"decision": forced_decision, "reason": forced_reason_hint}


# ---------------- AI Report (11 sections) ----------------

def generate_ai_report(tender_title, company_name, matched_results, compliance, risks, decision):
    prompt = f"""
Generate a complete tender bid analysis report with these EXACT 11 sections:
1. Executive Summary
2. Tender Overview
3. Company Overview
4. Compliance Summary
5. Matched Requirements
6. Missing Requirements
7. Unclear Requirements
8. Risk Analysis
9. Bid Recommendation
10. Key Reasons
11. Recommended Actions

DATA:
Tender: {tender_title}
Company: {company_name}
Matching Results: {matched_results}
Compliance: {compliance}
Risks: {risks}
Decision: {decision}

Return ONLY this JSON structure:
{{
  "executive_summary": "...",
  "tender_overview": "...",
  "company_overview": "...",
  "compliance_summary": "...",
  "matched_requirements": "...",
  "missing_requirements": "...",
  "unclear_requirements": "...",
  "risk_analysis": "...",
  "bid_recommendation": "...",
  "key_reasons": "...",
  "recommended_actions": "..."
}}
"""
    result = ask_llm(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "Could not parse the AI response", "raw": result}


# ---------------- Submission Checklist ----------------

def generate_checklist(matched_results):
    """Build an actionable checklist from Document-category requirements."""
    checklist = []
    for r in matched_results:
        if r.get("category") == "Documents":
            status = "checked" if r.get("status") == "Matched" else "unchecked"
            checklist.append({
                "item": r.get("requirement"),
                "status": status,
                "priority": r.get("priority")
            })
    return checklist


# ---------------- Main Pipeline ----------------

def run_full_analysis(analysis_output):
    """
    Run the complete bid-readiness pipeline:
    matching -> compliance -> risk -> decision -> report -> checklist.
    """
    print("Step 1: Matching requirements...")
    matched_results = match_all_requirements(analysis_output)

    print("Step 2: Calculating compliance...")
    compliance = calculate_compliance(matched_results)

    print("Step 3: Analyzing risks...")
    risks = analyze_risks(matched_results, analysis_output["tender_title"])

    print("Step 4: Making the bid decision...")
    decision = bid_decision(matched_results, compliance, risks)

    print("Step 5: Generating the AI report...")
    report = generate_ai_report(
        analysis_output["tender_title"],
        analysis_output["company_info"]["name"],
        matched_results, compliance, risks, decision
    )

    print("Step 6: Generating the submission checklist...")
    checklist = generate_checklist(matched_results)

    return {
        "matched_results": matched_results,
        "compliance": compliance,
        "risks": risks,
        "decision": decision,
        "report": report,
        "checklist": checklist
    }


# ---------------- Standalone test (only runs if this file is executed directly) ----------------

if __name__ == "__main__":
    result = run_full_analysis(SAMPLE_INPUT)
    print(json.dumps(result, indent=2))
