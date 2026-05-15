#!/usr/bin/env python3
"""Execute schema files against the Slingshot Supabase Postgres.

NOTE: db password is loaded from env var SUPABASE_DB_PASSWORD to avoid
checking it into git. Pass it via the SUPABASE_DB_PASSWORD env var when
running this script.
"""
import os
import sys
import psycopg2

PROJECT_REF = "euhymovdzlzzxukwcuqe"
PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD")
if not PASSWORD:
    print("ERROR: set SUPABASE_DB_PASSWORD env var")
    sys.exit(1)

# Try direct connection first; pooler as fallback
CONNECTION_STRINGS = [
    f"postgresql://postgres:{PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres?sslmode=require",
    f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-west-1.pooler.supabase.com:5432/postgres?sslmode=require",
    f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require",
    f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require",
]

def connect():
    last_err = None
    for cs in CONNECTION_STRINGS:
        try:
            print(f"trying: {cs.split('@')[1].split('/')[0]}")
            conn = psycopg2.connect(cs, connect_timeout=10)
            print(f"  ✓ connected via {cs.split('@')[1].split('/')[0]}")
            return conn
        except Exception as e:
            print(f"  ✗ {e}")
            last_err = e
    raise SystemExit(f"all connection attempts failed: {last_err}")

def main():
    schema_path = os.path.join(os.path.dirname(__file__), "001_init.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = connect()
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(sql)
        print("✓ schema applied")
    except Exception as e:
        print(f"✗ schema error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    # Verify tables exist
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
      select table_name from information_schema.tables
      where table_schema = 'public' order by table_name
    """)
    rows = cur.fetchall()
    print(f"\npublic schema tables ({len(rows)}):")
    for r in rows:
        print(f"  - {r[0]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
