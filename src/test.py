import chromadb
from chromadb.config import Settings
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"

# Use PersistentClient
client = chromadb.PersistentClient(
    path=str(DB_PATH),
    settings=chromadb.config.Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(name="hallucination_detector")

print("Total docs in collection:", collection.count())
print("Peek:", collection.peek())

tests = [
    {
        "name": "General Evidence",
        "query": "Does fine-tuning large language models reduce hallucinations in biomedical research?",
        "filter": None
    },
    {
        "name": "Metadata Filter (arXiv only)",
        "query": "Hallucination detection methods for research papers",
        "filter": {"source": "arxiv"}
    },
    {
        "name": "Journal Policy",
        "query": "What do journals recommend for verifying AI-generated content?",
        "filter": {"doc_type": "journal_guideline"}
    }
]

for t in tests:
    print("\n==============================")
    print("TEST:", t["name"])
    print("QUERY:", t["query"])

    results = collection.query(
        query_texts=[t["query"]],
        n_results=3,
        where=t["filter"]
    )

    docs = results.get("documents", [[]])[0]

    if not docs:
        print("⚠️ No documents retrieved. Check if your DB has relevant data for this filter.")
    else:
        for i, doc in enumerate(docs):
            print(f"\nResult {i+1}:\n{doc[:400]}...")