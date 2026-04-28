FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UPSKIN_PROJECT_ROOT=/app

COPY requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements-api.txt

COPY upskin_api /app/upskin_api
COPY stale.md /app/stale.md
COPY docs/backend_api_contract.md /app/docs/backend_api_contract.md
COPY artifacts /app/artifacts

EXPOSE 8000

CMD ["uvicorn", "upskin_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

