FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/text-extractor/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY apps/text-extractor/app/. ./

CMD ["python", "-u", "main.py"]
