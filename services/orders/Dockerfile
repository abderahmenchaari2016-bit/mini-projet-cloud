FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown -R app:app /app /data

COPY --chown=app:app app.py .

USER app
EXPOSE 8002

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8002", "app:app"]
