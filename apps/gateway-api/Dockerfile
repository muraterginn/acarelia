# acarelia/apps/gateway-api/Dockerfile

FROM python:3.11-slim
WORKDIR /app

# 1) requirements
COPY apps/gateway-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) ortak modüller
COPY common ./common

# 3) uygulama kodu
COPY apps/gateway-api/app ./app

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
