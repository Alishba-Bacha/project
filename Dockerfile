FROM python:3.10-slim

WORKDIR /app

# Copy only requirements first (layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . .

# No secrets inside image
ENV PYTHONUNBUFFERED=1

CMD ["python", "run_eval.py"]