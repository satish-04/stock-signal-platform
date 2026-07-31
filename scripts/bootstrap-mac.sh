#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { echo "Install Docker Desktop first."; exit 1; }
[ -f .env ] || cp .env.example .env
python3 - <<'PY'
from pathlib import Path
import secrets
p=Path('.env')
s=p.read_text()
s=s.replace('TRADINGVIEW_WEBHOOK_SECRET=replace-with-long-random-secret', 'TRADINGVIEW_WEBHOOK_SECRET='+secrets.token_urlsafe(32))
p.write_text(s)
PY
docker compose build
docker compose up -d
sleep 5
curl -fsS http://localhost:8080/health
printf '\nStarted. API docs: http://localhost:8080/docs\nGrafana: http://localhost:3000 (admin/admin)\n'
