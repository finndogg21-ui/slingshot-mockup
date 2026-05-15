#!/usr/bin/env python3
"""Create the 3 Slingshot user accounts via Supabase admin API,
then insert matching team_members rows.

Env required:
  SUPABASE_DB_PASSWORD   - postgres password (for team_members insert)
  SUPABASE_SERVICE_KEY   - service_role key (for admin API auth)
"""
import os
import sys
import json
import urllib.request
import psycopg2

PROJECT_REF = "euhymovdzlzzxukwcuqe"
PROJECT_URL = f"https://{PROJECT_REF}.supabase.co"
DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not DB_PASSWORD or not SERVICE_KEY:
    print("ERROR: set SUPABASE_DB_PASSWORD and SUPABASE_SERVICE_KEY env vars")
    sys.exit(1)

USERS = [
    {
        "email": "finndoggblox@gmail.com",
        "password": "Slingshot-Finnley-2026!",
        "name": "Finnley",
        "role": "Lead",
        "initials": "FO",
        "grad": "av-finnley",
    },
    {
        "email": "finndoggblox+matthew@gmail.com",
        "password": "Slingshot-Matthew-2026!",
        "name": "Matthew",
        "role": "Team",
        "initials": "MA",
        "grad": "av-matthew",
    },
    {
        "email": "finndoggblox+hudson@gmail.com",
        "password": "Slingshot-Hudson-2026!",
        "name": "Hudson",
        "role": "Team",
        "initials": "HU",
        "grad": "av-hudson",
    },
]

def create_user(email, password):
    """Create user via Supabase admin API. Returns user_id."""
    payload = json.dumps({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{PROJECT_URL}/auth/v1/admin/users",
        data=payload,
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read())
            return body.get("id")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if "User already registered" in body or "email_exists" in body or e.code == 422:
            # User exists — look it up
            return lookup_user_id(email)
        raise SystemExit(f"create_user({email}) failed: {e.code} {body}")

def lookup_user_id(email):
    """List users, find the one with matching email."""
    req = urllib.request.Request(
        f"{PROJECT_URL}/auth/v1/admin/users",
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read())
        for u in body.get("users", []):
            if u.get("email") == email:
                return u.get("id")
    raise SystemExit(f"could not find existing user for {email}")

def main():
    # Step 1: create users via auth admin API
    print("creating users...")
    for u in USERS:
        uid = create_user(u["email"], u["password"])
        u["user_id"] = uid
        print(f"  - {u['email']} -> {uid}")

    # Step 2: upsert team_members
    print("\nupserting team_members...")
    conn = psycopg2.connect(
        f"postgresql://postgres:{DB_PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres?sslmode=require",
        connect_timeout=10,
    )
    conn.autocommit = True
    cur = conn.cursor()
    for u in USERS:
        cur.execute("""
            insert into public.team_members (user_id, name, role, avatar_initials, avatar_grad)
            values (%s, %s, %s, %s, %s)
            on conflict (user_id) do update set
                name = excluded.name,
                role = excluded.role,
                avatar_initials = excluded.avatar_initials,
                avatar_grad = excluded.avatar_grad
            returning id
        """, (u["user_id"], u["name"], u["role"], u["initials"], u["grad"]))
        tm_id = cur.fetchone()[0]
        print(f"  - team_members[{u['name']}] -> {tm_id}")

    # Step 3: log activity
    cur.execute("""
        insert into public.activity (verb, target_type, summary)
        values ('seeded', 'team', 'Team initialized: Finnley, Matthew, Hudson')
    """)

    cur.close()
    conn.close()
    print("\n✓ seed complete")

if __name__ == "__main__":
    main()
