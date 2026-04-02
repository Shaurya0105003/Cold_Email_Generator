import streamlit as st
from chains import EmailChain
from portfolio import PortfolioStore
from scraper import scrape_url
from portfolio_data import DEFAULT_PORTFOLIO

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cold Email Generator",
    page_icon="✉️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'DM Serif Display', serif;
}

.stApp {
    background: #0e0e0e;
    color: #f0ede8;
}

section[data-testid="stSidebar"] {
    background: #141414;
    border-right: 1px solid #2a2a2a;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    color: #f0ede8 !important;
    border-radius: 8px !important;
}

.stButton > button {
    background: #d4a843;
    color: #0e0e0e;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #e8bf6a;
    transform: translateY(-1px);
}

.email-output {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-left: 3px solid #d4a843;
    border-radius: 8px;
    padding: 1.5rem;
    white-space: pre-wrap;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #f0ede8;
}

.job-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}

.tag {
    display: inline-block;
    background: #252525;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 2px 8px;
    margin: 2px;
    font-size: 0.75rem;
    color: #d4a843;
}

.section-label {
    color: #888;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Setup")
    st.markdown("---")

    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get your free key at console.groq.com",
    )

    st.markdown("### Upload Resume")
    st.caption("Upload your PDF — name, role, company, and portfolio will be filled automatically.")
    resume_file = st.file_uploader("Resume (PDF)", type=["pdf"])

    if resume_file and groq_api_key:
        if st.button("Parse Resume"):
            with st.spinner("Reading resume..."):
                try:
                    import pypdf
                    import io
                    pdf_bytes = resume_file.read()
                    text = ""
                    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                    for page in reader.pages:
                        text += page.extract_text() or ""

                    chain_temp = EmailChain(groq_api_key)
                    parsed = chain_temp.parse_resume(text)

                    st.session_state["parsed_resume"] = parsed
                    if parsed.get("_parse_error"):
                        st.warning("Partially parsed — some fields may be empty. Fill in manually.")
                    else:
                        st.success("Resume parsed!")
                except ImportError:
                    st.error("Run: pip install pypdf")
                except Exception as e:
                    st.error(f"Parse error: {e}")

    # Use parsed values if available, else blank
    parsed = st.session_state.get("parsed_resume", {})

    st.markdown("### Your Details")
    sender_name = st.text_input(
        "Your Name",
        value=parsed.get("name", ""),
        placeholder="Shaurya Malviya",
    )
    sender_role = st.text_input(
        "Your Role",
        value=parsed.get("role", ""),
        placeholder="AI Engineer / GTM Lead",
    )
    company_name = st.text_input(
        "Your Company",
        value=parsed.get("company", ""),
        placeholder="Eazybe",
    )

    st.markdown("---")
    st.markdown("### Portfolio")

    # Auto-parsed portfolio from resume
    resume_portfolio = parsed.get("portfolio", [])

    if resume_portfolio:
        st.caption(f"Auto-populated {len(resume_portfolio)} entries from your resume. Edit below if needed.")
        portfolio_items = []
        for i, item in enumerate(resume_portfolio):
            with st.expander(f"Entry {i+1}", expanded=False):
                tech = st.text_input(
                    "Tech Stack",
                    value=item.get("techstack", ""),
                    key=f"tech_{i}",
                )
                link = st.text_input(
                    "Link",
                    value=item.get("links", ""),
                    key=f"link_{i}",
                )
                if tech:
                    portfolio_items.append({"techstack": tech, "links": link})
    else:
        st.caption("Upload a resume above to auto-populate, or add manually.")
        portfolio_items = []
        num_items = st.number_input("Number of portfolio items", 1, 10, 3)
        for i in range(int(num_items)):
            with st.expander(f"Project {i+1}", expanded=(i == 0)):
                tech = st.text_input(
                    "Tech Stack",
                    key=f"tech_{i}",
                    placeholder="Python, LangChain, RAG, ChromaDB",
                )
                link = st.text_input(
                    "Link",
                    key=f"link_{i}",
                    placeholder="https://github.com/yourname/project",
                )
                if tech:
                    portfolio_items.append({"techstack": tech, "links": link})

    if not portfolio_items:
        st.caption("Using default portfolio as fallback.")
        portfolio_items = DEFAULT_PORTFOLIO

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# Cold Email Generator")
st.markdown(
    "<p style='color:#888; margin-top:-0.5rem;'>Paste a job URL or raw JD text → get a human-written cold email matched to your portfolio.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

input_method = st.radio(
    "Input method",
    ["🔗 Job Posting URL", "📋 Paste JD Text"],
    horizontal=True,
)

job_text = ""

if input_method == "🔗 Job Posting URL":
    url = st.text_input("Job Posting URL", placeholder="https://jobs.ashbyhq.com/...")
    if st.button("Scrape & Load"):
        if not url:
            st.warning("Please enter a URL.")
        else:
            with st.spinner("Scraping job posting..."):
                try:
                    job_text = scrape_url(url)
                    st.session_state["job_text"] = job_text
                    st.success(f"Scraped {len(job_text)} characters.")
                except Exception as e:
                    st.error(str(e))
else:
    raw = st.text_area(
        "Paste Job Description",
        height=250,
        placeholder="Paste the full job description here...",
    )
    if raw:
        st.session_state["job_text"] = raw

# Use session state text if available
if "job_text" in st.session_state:
    job_text = st.session_state["job_text"]

# ── Generate ──────────────────────────────────────────────────────────────────
if st.button("✉️ Generate Cold Email", use_container_width=True):
    if not groq_api_key:
        st.error("Add your Groq API key in the sidebar first.")
    elif not job_text:
        st.error("Load a job posting first.")
    elif not sender_name or not sender_role or not company_name:
        st.warning("Fill in your name, role, and company in the sidebar.")
    else:
        try:
            chain = EmailChain(groq_api_key)
            store = PortfolioStore()
            store.load_portfolio(portfolio_items)

            with st.spinner("Extracting job details..."):
                jobs = chain.extract_jobs(job_text)

            if not jobs:
                st.error("Could not extract job information. Try pasting cleaner JD text.")
            else:
                # Show parsed job cards
                st.markdown("### Detected Job(s)")
                for i, job in enumerate(jobs):
                    with st.container():
                        st.markdown(
                            f"""
<div class='job-card'>
<div class='section-label'>Role</div>
<strong>{job.get('role', 'N/A')}</strong><br><br>
<div class='section-label'>Experience</div>
{job.get('experience', 'N/A')}<br><br>
<div class='section-label'>Skills</div>
{"".join(f"<span class='tag'>{s}</span>" for s in job.get('skills', []))}
</div>
""",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")
                st.markdown("### Generated Email(s)")

                for i, job in enumerate(jobs):
                    skills = job.get("skills", [])
                    links = store.query_links(skills)

                    with st.spinner(f"Writing email for: {job.get('role', 'Role')}..."):
                        email = chain.write_email(
                            job=job,
                            portfolio_links=links,
                            sender_name=sender_name,
                            sender_role=sender_role,
                            company_name=company_name,
                        )

                    st.markdown(f"**{job.get('role', f'Role {i+1}')}**")
                    st.markdown(
                        f"<div class='email-output'>{email}</div>",
                        unsafe_allow_html=True,
                    )

                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.download_button(
                            "⬇ Download",
                            data=email,
                            file_name=f"cold_email_{i+1}.txt",
                            mime="text/plain",
                        )
                    st.markdown("")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
