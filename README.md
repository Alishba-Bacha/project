# Quick README template
@"
# Capstone Project

## Setup
1. Clone this repo
2. Copy `.env.example` to `.env` and add your keys
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python run_eval.py`

## Required Environment Variables
- `LANGCHAIN_API_KEY`: Your LangChain API key
- `OLLAMA_HOST`: Ollama server URL
"@ | Out-File -FilePath README.md -Encoding UTF8
