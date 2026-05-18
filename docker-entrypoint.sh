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

echo "[entrypoint] Checking if seed data is needed..."
python - <<'PYEOF'
import os, psycopg2

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM pipeline_runs")
count = cur.fetchone()[0]
conn.close()

if count == 0:
    print(f"[entrypoint] Table is empty — seeding mock data...")
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "simulator/mock_pipeline.py"],
        capture_output=False,
    )
    sys.exit(result.returncode)
else:
    print(f"[entrypoint] Found {count} existing rows — skipping seed.")
PYEOF

echo "[entrypoint] Starting process: $@"
exec "$@"