#!/usr/bin/env sh
# Wait until a TCP host:port accepts connections, or give up.
#
# Usage: wait-for.sh <host> <port> [timeout-seconds]
#
# Compose `depends_on: {condition: service_healthy}` already orders startup, so
# this is a belt-and-braces guard for `docker compose run` and for the window
# between "container healthy" and "socket accepting" after a restart.
set -eu

host="${1:?usage: wait-for.sh <host> <port> [timeout]}"
port="${2:?usage: wait-for.sh <host> <port> [timeout]}"
timeout="${3:-60}"

elapsed=0
while [ "$elapsed" -lt "$timeout" ]; do
  if python -c "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0 if s.connect_ex(('$host', $port))==0 else 1)" 2>/dev/null; then
    exit 0
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

echo "wait-for: timed out after ${timeout}s waiting for ${host}:${port}" >&2
exit 1
