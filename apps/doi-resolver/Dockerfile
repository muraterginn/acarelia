FROM python:3.11-slim

WORKDIR /opt/acarelia/apps/doi-resolver

COPY apps/doi-resolver/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/doi-resolver/app ./app
COPY common             ./common

CMD ["python", "-u", "-m", "app.main"]