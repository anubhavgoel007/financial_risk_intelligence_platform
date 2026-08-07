# ---- Builder stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src ./src

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

USER appuser

EXPOSE 8000

CMD ["uvicorn", "risk_platform.main:app", "--host", "0.0.0.0", "--port", "8000"]
