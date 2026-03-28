FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/uploads

EXPOSE 8080

CMD ["sh", "-c", "gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:${PORT} server:app"]
