FROM python:3.11-slim

WORKDIR /opt/acarelia/apps/ai-analyzer

COPY apps/ai-analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/ai-analyzer/app /opt/acarelia/apps/ai-analyzer/app
COPY common               /opt/acarelia/common

ENV PYTHONPATH=/opt/acarelia
CMD ["python", "-u", "-m", "app.main"]