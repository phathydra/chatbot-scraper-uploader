FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py .
COPY uploader.py .
COPY main.py .

RUN mkdir -p /data

CMD ["python", "main.py"]