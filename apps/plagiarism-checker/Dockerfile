FROM python:3.11-slim

WORKDIR /opt/acarelia/apps/plagiarism-checker

RUN apt-get update && \
    apt-get install -y gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY ../../common /opt/acarelia/common

COPY apps/plagiarism-checker/app /opt/acarelia/apps/plagiarism-checker/app

COPY apps/plagiarism-checker/requirements.txt /opt/acarelia/apps/plagiarism-checker/requirements.txt

ENV PYTHONPATH="/opt/acarelia:${PYTHONPATH}"

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/main.py"]