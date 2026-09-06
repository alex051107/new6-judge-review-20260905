FROM python:3.11.16-slim-bookworm@sha256:528257d48c1da0dcecc2e725d1ae34498d60c965f1241e39cd6a85a8859bdf84
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-calc=4:7.4.7-1+deb12u14 \
    fonts-liberation=1:1.07.4-11 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp LANG=C.UTF-8 TZ=UTC
WORKDIR /workspace
