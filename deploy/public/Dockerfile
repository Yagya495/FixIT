# Public, anonymous FixIt Madison demo (PUBLIC_DEMO=true): SQLite + synthetic data + saved/scripted Demo Mode results.
# No Databricks credentials are used or needed. Same layout as the Databricks App bundle (`make bundle`).
# Build from the repo root:  docker build -f deploy/public/Dockerfile -t fixit-public .
# Run locally:               docker run --rm -p 8000:8000 fixit-public   -> http://localhost:8000

FROM node:22-slim AS web
WORKDIR /web
COPY app/frontend/package.json app/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY app/frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PUBLIC_DEMO=true DEMO_MODE=true DATA_BACKEND=local FIXIT_DATA_DIR=/tmp/fixit-data
WORKDIR /srv/app
COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/backend ./backend
RUN rm -rf backend/tests
COPY --from=web /web/dist ./static
COPY demo/cached_outputs ./demo/cached_outputs
RUN useradd --create-home --uid 10001 fixit && mkdir -p /tmp/fixit-data && chown fixit /tmp/fixit-data
USER fixit
# Hosts such as Render set $PORT; the DB is reseeded from the synthetic generator on every start (ephemeral disk).
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
