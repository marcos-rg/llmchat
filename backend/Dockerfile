# Build context is the repo ROOT (not ./backend) so scripts/wait-for.sh, which is
# shared with the host-side tooling, can be baked into the image. See
# docker-compose.yml -> x-backend-image.
#
# Two stages, and `dev` is deliberately the LAST one so a plain `docker compose
# build` (which names no target) produces the image the test targets need. The
# split exists so `requirements/dev.txt` — pytest, ruff, factory_boy — is a layer
# that a future `--target runtime` build simply does not have, rather than a
# comment promising nobody installed it.
FROM python:3.12-slim AS runtime

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

# --- dev ---------------------------------------------------------------------
# Adds the test/lint toolchain. dev.txt starts with `-r base.txt`, which is
# already satisfied above, so this layer only downloads the tooling itself.
FROM runtime AS dev

COPY backend/requirements/dev.txt /tmp/requirements/dev.txt
RUN pip install --no-cache-dir -r /tmp/requirements/dev.txt
