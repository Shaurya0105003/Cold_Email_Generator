# Cold Email Generator — GenAI Product

A Streamlit app that takes a job posting URL or pasted JD text, extracts structured job info using **Llama 3.1 via Groq**, matches your portfolio using **ChromaDB semantic search**, and writes a human-sounding cold outreach email.

---

## Stack

| Layer | Tech |
|---|---|
| LLM | Llama 3.1 8B via Groq API |
| Orchestration | LangChain |
| Vector Store | ChromaDB |
| Embeddings | Sentence Transformers |
| Web Scraping | BeautifulSoup + Requests |
| UI | Streamlit |

---

## Setup

### 1. Clone / navigate to this folder
```bash
cd cold_email_generator
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key
Go to [console.groq.com](https://console.groq.com) → Sign up → API Keys → Create Key  
It's free. No credit card needed.

### 4. Run
```bash
streamlit run app.py
```

---

## How to use

1. Enter your **Groq API key** in the sidebar
2. Fill in your **name, role, and company**
3. Add your **portfolio projects** (tech stack + GitHub link)
4. Either paste a **job posting URL** or paste the **JD text** directly
5. Click **Generate Cold Email**

---

## File Structure

```
cold_email_generator/
├── app.py              # Streamlit UI
├── chains.py           # LangChain + Groq: JD extraction + email generation
├── portfolio.py        # ChromaDB vector store for portfolio matching
├── scraper.py          # BeautifulSoup web scraper
├── portfolio_data.py   # Default sample portfolio items
└── requirements.txt
```

---

## Notes

- Works best with **Llama 3.1 8b-instant** (fast, free on Groq)
- If a job URL blocks scraping, paste the JD text directly
- Edit `portfolio_data.py` to set default portfolio items