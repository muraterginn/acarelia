# 1) Base image
FROM python:3.11-slim

# 2) Çalışma dizini
WORKDIR /app

# 3) Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Uygulama kodunu kopyala
COPY app/ ./app
COPY test_playwright_scraper.py ./

# 5) Çalıştırma komutu
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
