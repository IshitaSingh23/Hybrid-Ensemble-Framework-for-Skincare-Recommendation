FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UPSKIN_PROJECT_ROOT=/app
ENV UPSKIN_MODEL_RUN_ID=v002
ENV UPSKIN_CORS_ORIGINS=https://up-skin.vercel.app,https://up-skin.onrender.com
ENV PORT=8000

COPY requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements-api.txt

COPY upskin_api /app/upskin_api
COPY stale.md /app/stale.md
COPY docs/backend_api_contract.md /app/docs/backend_api_contract.md
COPY artifacts /app/artifacts

EXPOSE 8000

CMD ["sh", "-c", "uvicorn upskin_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
