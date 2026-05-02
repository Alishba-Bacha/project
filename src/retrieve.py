import chromadb
import httpx
from pathlib import Path

httpx.DEFAULT_TIMEOUT = httpx.Timeout(1300.0)  
DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"

# Use PersistentClient
client = chromadb.PersistentClient(
    path=str(DB_PATH),
    settings=chromadb.config.Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(name="hallucination_detector")

query = "Do fine-tuned LLMs reduce hallucinations in medical papers?"

results = collection.query(
    query_texts=[query],
    n_results=3
)
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print("\n---\n", doc[:500])
    print("Metadata:", meta)