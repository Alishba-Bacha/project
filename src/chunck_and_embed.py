from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def chunk_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks

def embed(text):
    return model.encode(text).tolist()

if __name__ == "__main__":
    with open("data/processed/cleaned_chunks.json") as f:
        docs = json.load(f)

    embedded = []

    for doc in tqdm(docs):
        chunks = chunk_text(doc["text"])

        for chunk in chunks:
            embedded.append({
                "text": chunk,
                "embedding": embed(chunk),
                "metadata": doc["metadata"]
            })

    with open("data/processed/embedded_chunks.json", "w") as f:
        json.dump(embedded, f)

    print("Embeddings with chunking created.")