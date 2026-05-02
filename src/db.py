import chromadb
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"

def get_collection(name="hallucination_detector"):
    client = chromadb.Client(
        chromadb.config.Settings(
            persist_directory=str(DB_PATH),
            anonymized_telemetry=False
        )
    )
    collection = client.get_or_create_collection(name=name)
    return collection, DB_PATH