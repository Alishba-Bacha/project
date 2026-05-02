import json
import chromadb
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"

# Use PersistentClient instead of Client with Settings
client = chromadb.PersistentClient(
    path=str(DB_PATH),
    settings=chromadb.config.Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(name="hallucination_detector")

# Load JSON data
with open("data/processed/embedded_chunks.json") as f:
    data = json.load(f)

# Prepare data lists
documents, embeddings, metadatas, ids = [], [], [], []

for i, item in enumerate(data):
    emb = item["embedding"]
    if not isinstance(emb, list):
        emb = emb.tolist()
    documents.append(item["text"])
    embeddings.append(emb)
    metadatas.append(item.get("metadata", {}))
    ids.append(f"doc_{i}")

# Add all items in a batch
collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)

print(f"Vector DB persisted successfully. Total documents: {collection.count()}")