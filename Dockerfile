FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Node.js + Codex CLI : rédige le brief du matin (voir app/brief_writer.py).
# Authentification via le login ChatGPT d'Eva, monté à l'exécution dans
# CODEX_HOME (voir compose.yaml) — pas de clé API à embarquer dans l'image.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @openai/codex \
    && apt-get purge -y curl gnupg && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY app/ app/
COPY viz/ viz/

ENV RUN_SCHEDULER=1
ENV CODEX_HOME=/srv/.codex
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
