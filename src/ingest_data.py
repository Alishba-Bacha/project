import re
import json
from pathlib import Path
from pypdf import PdfReader
from tqdm import tqdm

RAW_DIR = "data/raw"
OUT_FILE = "data/processed/cleaned_chunks.json"

def clean_text(text):
    text = re.sub(r"arXiv:\d+\.\d+v\d+", "", text)
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def process_pdfs(folder, source, field):
    docs = []
    for pdf in Path(folder).glob("*.pdf"):
        reader = PdfReader(pdf)
        text = ""
        for p in reader.pages:
            text += p.extract_text() + "\n"

        docs.append({
            "text": clean_text(text),
            "metadata": {
                "doc_type": "research_paper",
                "source": source,
                "field": field,
                "year": "2024",
                "paper_id": pdf.stem
            }
        })
    return docs

if __name__ == "__main__":
    all_docs = []
    all_docs += process_pdfs("data/raw/arxiv_papers", "arxiv", "cs")
    all_docs += process_pdfs("data/raw/journal_guidelines", "journal", "policy")

    Path("data/processed").mkdir(exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(all_docs, f, indent=2)

    print(f"Ingested {len(all_docs)} documents.")
    