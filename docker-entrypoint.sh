set -e

echo "[entrypoint] Waiting for PostgreSQL to be ready..."
until python - <<'PYEOF'
import os, psycopg2
try:
    psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    ).close()
    print("PostgreSQL is ready.")
except Exception:
    exit(1)
PYEOF
do
  echo "[entrypoint] PostgreSQL not ready — retrying in 2s..."
  sleep 2
done