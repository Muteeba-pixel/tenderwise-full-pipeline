import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY=os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client=genai.Client(api_key=API_KEY)

MODEL="gemini-3.6-flash"


def prepare_document_text(document_data):
    text=""

    for chunk in document_data["chunks"]:
        text+=(
            f"\n\nDOCUMENT: {chunk['document']}"
            f"\nPAGE: {chunk['page']}"
            f"\nTEXT: {chunk['text']}"
        )

    return text


def generate_json(prompt,schema):
    interaction=client.interactions.create(
        model=MODEL,
        input=prompt,
        response_format={
            "type":"text",
            "mime_type":"application/json",
            "schema":schema
        }
    )

    return json.loads(interaction.output_text)


def analyze_tender(tender_data):

    tender_text=prepare_document_text(tender_data)

    schema={
        "type":"object",
        "properties":{
            "tender_title":{"type":"string"},
            "tender_category":{"type":"string"},
            "deadline":{"type":"string"},
            "requirements":{
                "type":"array",
                "items":{
                    "type":"object",
                    "properties":{
                        "requirement":{"type":"string"},
                        "category":{"type":"string"},
                        "priority":{"type":"string"},
                        "evidence":{
                            "type":"object",
                            "properties":{
                                "text":{"type":"string"},
                                "page":{"type":"integer"},
                                "document":{"type":"string"}
                            },
                            "required":["text","page","document"]
                        }
                    },
                    "required":[
                        "requirement",
                        "category",
                        "priority",
                        "evidence"
                    ]
                }
            }
        },
        "required":[
            "tender_title",
            "tender_category",
            "deadline",
            "requirements"
        ]
    }

    prompt=f"""
You are a professional tender analysis expert.

Analyze the tender document below.

Extract ONLY information that is supported by the document.

Extract:

1. Tender title
2. Tender category/type
3. Deadline
4. Eligibility requirements
5. Technical requirements
6. Experience requirements
7. Financial requirements
8. Certifications
9. Required documents
10. Other important requirements

Put every requirement inside the requirements array.

For every requirement provide:

- requirement
- category
- priority
- evidence

Categories:
Eligibility
Technical
Experience
Financial
Certification
Documents
Other

Priority:
Mandatory
Important
Optional
Unclear

The evidence MUST come from the provided text.

Preserve the exact page number and document name.

Never invent information.

If information is unavailable, write "Not specified".

TENDER DOCUMENT:

{tender_text}
"""

    return generate_json(prompt,schema)


def analyze_company(company_data):

    company_text=prepare_document_text(company_data)

    schema={
        "type":"object",
        "properties":{
            "company_name":{"type":"string"},
            "services":{
                "type":"array",
                "items":{"type":"string"}
            },
            "experience":{
                "type":"array",
                "items":{"type":"string"}
            },
            "certifications":{
                "type":"array",
                "items":{"type":"string"}
            },
            "projects":{
                "type":"array",
                "items":{"type":"string"}
            },
            "technical_capabilities":{
                "type":"array",
                "items":{"type":"string"}
            },
            "financial_information":{
                "type":"array",
                "items":{"type":"string"}
            },
            "registrations":{
                "type":"array",
                "items":{"type":"string"}
            },
            "relevant_expertise":{
                "type":"array",
                "items":{"type":"string"}
            }
        },
        "required":[
            "company_name",
            "services",
            "experience",
            "certifications",
            "projects",
            "technical_capabilities",
            "financial_information",
            "registrations",
            "relevant_expertise"
        ]
    }

    prompt=f"""
You are a professional company profile analysis expert.

Analyze the company profile below.

Extract ONLY information supported by the document.

Extract:

- Company name
- Services
- Experience
- Certifications
- Projects
- Technical capabilities
- Financial information
- Registrations
- Relevant expertise

Do not invent information.

If information is unavailable, use an empty list or "Not specified".

COMPANY PROFILE:

{company_text}
"""

    return generate_json(prompt,schema)


def analyze_documents(tender_data,company_data):

    tender_analysis=analyze_tender(tender_data)

    company_analysis=analyze_company(company_data)

    return {
        "tender_analysis":tender_analysis,
        "company_analysis":company_analysis
    }