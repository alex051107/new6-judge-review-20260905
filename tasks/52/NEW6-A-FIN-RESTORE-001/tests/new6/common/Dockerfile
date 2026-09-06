FROM p15-agent-base:harbor-0.22.0-agentset-1
# Reuse the previously installed CLI set, add only spreadsheet/PDF runtime.
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-calc fonts-liberation poppler-utils \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir openpyxl==3.1.5 pandas==2.3.3 pypdf==6.0.0 pymupdf==1.26.4 lxml==6.0.1
WORKDIR /app
RUN mkdir -p /app/input /app/output /logs/verifier
