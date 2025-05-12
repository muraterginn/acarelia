FROM python:3.11-slim
WORKDIR /app

# 1) requirements.txt’in tam yolu
COPY apps/scholar-scraper/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) common klasörünü kopyala
COPY common ./common

# 3) scraper uygulamasını kopyala
COPY apps/scholar-scraper/app ./app

ENV PYTHONPATH=/app

CMD ["python", "-u", "app/worker.py"]
