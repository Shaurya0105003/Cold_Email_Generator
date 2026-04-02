from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import re
import json


class EmailChain:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=groq_api_key,
            model_name="llama-3.1-8b-instant",
        )

    def extract_jobs(self, cleaned_text: str) -> list[dict]:
        """
        Parse job description text and return structured job info as a list of dicts.
        Each dict has: role, experience, skills, description
        """
        prompt = PromptTemplate.from_template(
            """
### JOB DESCRIPTION TEXT:
{page_data}

### INSTRUCTION:
Extract the job postings from the above text. Return a JSON array (list) of objects.
Each object must have these fields:
- "role": job title
- "experience": required experience
- "skills": list of required skills/technologies
- "description": brief job summary

Only return valid JSON. No preamble, no explanation, no markdown.
            """
        )
        chain = prompt | self.llm | JsonOutputParser()
        try:
            return chain.invoke({"page_data": cleaned_text})
        except OutputParserException:
            raise ValueError("Could not parse job description. Try pasting cleaner text.")

    def parse_resume(self, resume_text: str) -> dict:
        """
        Parse a resume and extract:
        - name, linkedin, github, email, role, company
        - portfolio items: list of {techstack, links}
        LinkedIn is used as fallback link if no GitHub/project link found.
        """
        # Use a stronger model just for parsing
        llm_strong = ChatGroq(
            temperature=0,
            groq_api_key=self.groq_api_key,
            model_name="llama-3.3-70b-versatile",
        )

        resume_text = resume_text[:4000]

        prompt = PromptTemplate.from_template(
            """You are a resume parser. Extract information from the resume below and return ONLY a JSON object. No explanation, no markdown, no code fences, just raw JSON.

RESUME:
{resume_text}

Return this exact structure:
{{
  "name": "full name",
  "email": "email address or empty string",
  "linkedin": "linkedin URL or empty string",
  "github": "github URL or empty string",
  "role": "most recent job title",
  "company": "most recent company name",
  "portfolio": [
    {{
      "techstack": "comma separated tools and technologies",
      "links": "linkedin URL as fallback if no github link"
    }}
  ]
}}

Rules:
- One portfolio entry per job experience, one per project
- For links: use LinkedIn URL as fallback if no direct GitHub project link exists
- Return ONLY the raw JSON object. No text before or after it."""
        )

        chain = prompt | llm_strong
        result = chain.invoke({"resume_text": resume_text})
        raw = result.content.strip()

        # Strip markdown fences if present
        raw = re.sub(r"```json", "", raw)
        raw = re.sub(r"```", "", raw)
        raw = raw.strip()

        # Extract JSON object even if there's surrounding text
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group(0)

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            return {
                "name": "",
                "email": "",
                "linkedin": "",
                "github": "",
                "role": "",
                "company": "",
                "portfolio": [],
                "_parse_error": str(e),
            }

    def write_email(
        self,
        job: dict,
        portfolio_links: list[str],
        sender_name: str,
        sender_role: str,
        company_name: str,
    ) -> str:
        """
        Generate a cold outreach email for a given job posting.
        """
        links_str = "\n".join(portfolio_links) if portfolio_links else "N/A"

        prompt = PromptTemplate.from_template(
            """
### JOB ROLE: {job_role}
### JOB DESCRIPTION: {job_description}
### REQUIRED SKILLS: {skills}

### YOUR PORTFOLIO LINKS (relevant projects):
{portfolio_links}

### INSTRUCTION:
You are {sender_name}, a {sender_role} at {company_name}.

Write a cold outreach email to the hiring manager for the above role.

Guidelines:
- Sound like a real human wrote this — no buzzwords, no hollow phrases
- Be concise: 3–4 short paragraphs max
- Reference 1–2 specific skills from the JD naturally
- Mention the portfolio links where relevant, don't list them robotically
- End with a low-pressure CTA (a quick call or reply)
- Subject line at the top, then the email body
- Do NOT use phrases like "I hope this email finds you well", "I wanted to reach out", "cutting-edge", "passionate", "leverage", "synergy"

Only output the subject line and email. No labels, no extra commentary.
            """
        )
        chain = prompt | self.llm
        result = chain.invoke(
            {
                "job_role": job.get("role", ""),
                "job_description": job.get("description", ""),
                "skills": ", ".join(job.get("skills", [])),
                "portfolio_links": links_str,
                "sender_name": sender_name,
                "sender_role": sender_role,
                "company_name": company_name,
            }
        )
        return result.content