# NetPulse backend (FastAPI + SNMP/ICMP poller)
# Build context = repository root.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install curated production deps first (better layer caching)
COPY deploy/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# App code
COPY backend/ ./

EXPOSE 8001

# Uvicorn binds 0.0.0.0:8001; nginx (frontend container) proxies /api here.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
