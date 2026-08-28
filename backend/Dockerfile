# Build context is the repo ROOT (not ./backend) so scripts/wait-for.sh, which is
# shared with the host-side tooling, can be baked into the image. See
# docker-compose.yml -> x-backend-image.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# curl -> backend healthcheck; procps -> worker healthcheck (pgrep).
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl procps \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements/base.txt /tmp/requirements/base.txt
RUN pip install --no-cache-dir -r /tmp/requirements/base.txt

COPY scripts/wait-for.sh /usr/local/bin/wait-for.sh
COPY backend/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/wait-for.sh /usr/local/bin/entrypoint.sh

COPY backend/ /app/

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
