import chromadb
import uuid


class PortfolioStore:
    """
    Stores portfolio/resume bullet points as embeddings in ChromaDB.
    On query, returns the most relevant projects/skills for a given job description.
    """

    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name="portfolio")

    def load_portfolio(self, items: list[dict]):
        """
        items: list of dicts with keys 'techstack' and 'links'
        e.g. [{"techstack": "Python, LangChain, RAG", "links": "github.com/..."}]
        """
        if not self.collection.count():
            for item in items:
                self.collection.add(
                    documents=[item["techstack"]],
                    metadatas=[{"links": item["links"]}],
                    ids=[str(uuid.uuid4())],
                )

    def query_links(self, skills: list[str]) -> list[str]:
        if not skills:
            return []
        results = self.collection.query(
            query_texts=skills,
            n_results=2,
        )
        links = []
        for meta_list in results.get("metadatas", []):
            for meta in meta_list:
                if meta.get("links"):
                    links.append(meta["links"])
        return list(set(links))