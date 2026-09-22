import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger("mplads.llm")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

async def generate_executive_explanation(project_data: Dict[str, Any]) -> str:
    """
    Connects to local Ollama instance to generate a 2-sentence executive audit explanation.
    Falls back to a structured rule-based explanation if Ollama is unreachable.
    """
    title = project_data.get("title", "Project")
    category = project_data.get("category", "Infrastructure")
    sanctioned = project_data.get("sanctioned_amount", 0)
    expenditure = project_data.get("expenditure_amount", 0)
    risk_score = project_data.get("risk_score", 0)
    contractor = project_data.get("contractor_name", "N/A")
    district = project_data.get("district_name", "N/A")
    anomalies = project_data.get("anomalies", [])

    prompt = (
        f"You are an AI Forensic Auditor for India's MPLAD Scheme. Analyze this project:\n"
        f"Title: {title}\n"
        f"District: {district}, Category: {category}\n"
        f"Contractor: {contractor}\n"
        f"Sanctioned: INR {sanctioned:,.2f}, Expenditure: INR {expenditure:,.2f}\n"
        f"Risk Score: {risk_score}/100\n"
        f"Detected Anomalies: {', '.join(anomalies) if anomalies else 'None'}\n\n"
        f"Provide EXACTLY a 2-sentence executive audit summary explaining why this project was flagged and recommending action."
    )

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "max_tokens": 120}
                }
            )
            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "").strip()
                if text:
                    return text
    except Exception as e:
        logger.info(f"Ollama local service unavailable ({e}). Using rule-based fallback generator.")

    # Rule-based fallback generator (produces exact 2-sentence audit report)
    cost_overrun = expenditure - sanctioned
    if anomalies:
        primary_anomaly = anomalies[0]
        sentence1 = f"Project '{title}' in {district} has been assigned a critical risk score of {risk_score:.1f}/100 due to detected {primary_anomaly.lower()} involving contractor {contractor}."
        if cost_overrun > 0:
            sentence2 = f"With a total expenditure overrun of INR {cost_overrun:,.2f}, immediate physical site inspection and disbursement freezing are strongly advised."
        else:
            sentence2 = f"Given the compliance flags raised across {category} allocation patterns, an administrative review by the District Nodal Officer is required."
    else:
        sentence1 = f"Project '{title}' in {district} exhibits normal expenditure variance with a low risk rating of {risk_score:.1f}/100."
        sentence2 = "No critical compliance anomalies were flagged during automated ML inspection, approving it for routine tranche releases."

    return f"{sentence1} {sentence2}"
