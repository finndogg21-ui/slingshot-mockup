#!/usr/bin/env python3
"""Seed initial Slingshot tasks for Finnley, Matthew, Hudson."""
import os
import sys
import psycopg2

PROJECT_REF = "euhymovdzlzzxukwcuqe"
DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD")
if not DB_PASSWORD:
    print("ERROR: set SUPABASE_DB_PASSWORD env var")
    sys.exit(1)

# Real tasks based on current Slingshot state (May 15, 2026)
TASKS = [
    # Finnley - blocking + admin
    {
        "title": "Sign the 3-way revenue split agreement",
        "outcome": "All three of us have signed a written agreement defining how Robux/USD earnings are split. One of us (Finnley) is the verified account holder for DevEx; the agreement papers this so the first payout doesn't end the friendship.",
        "acceptance": "Signed PDF stored in Obsidian vault. Status confirmed by Matthew + Hudson in comments.",
        "category": "admin",
        "assignee": "Finnley",
        "priority": "urgent",
        "due_offset_days": -2,  # overdue
    },
    {
        "title": "Set up Roblox Premium + verified ID for DevEx",
        "outcome": "DevEx pipeline is ready so that when the first game earns 30,000 Robux, payout can be requested without scrambling for ID verification.",
        "acceptance": "Roblox Premium active on the verified account. DevEx settings show ID verification status as 'Approved'.",
        "category": "admin",
        "assignee": "Finnley",
        "priority": "high",
        "due_offset_days": 0,
    },
    {
        "title": "Validate Hello World loop: Claude Code + Roblox Studio MCP",
        "outcome": "A part in a test Roblox Studio place that says 'Hi <player>' when touched, written entirely by Claude via the Studio MCP. End-to-end loop proven before committing to Game 1.",
        "acceptance": "Screenshot of the working part in Studio. Time-to-completion logged in this task's comments.",
        "category": "meta",
        "assignee": "Finnley",
        "priority": "high",
        "due_offset_days": 1,
    },

    # Matthew - onboarding
    {
        "title": "Watch a Roblox Studio intro tutorial (~2 hrs)",
        "outcome": "You can open Studio, navigate the Explorer panel, insert a Part, run a test session, and publish a place. You don't need to write code — you need to recognize the UI.",
        "acceptance": "Comment a 1-sentence note: 'I can open Studio and X' (where X is something concrete you did).",
        "category": "meta",
        "assignee": "Matthew",
        "priority": "high",
        "due_offset_days": 1,
    },
    {
        "title": "Decide your specialization: research or building?",
        "outcome": "Pick one: trend research (TikTok/YouTube scanning, IP vetting, concept generation) OR building (directing Claude via Studio MCP to make game systems). You can swap later, but pick a primary now so we can assign concrete work.",
        "acceptance": "Reply in this task's comments with your pick + why.",
        "category": "meta",
        "assignee": "Matthew",
        "priority": "medium",
        "due_offset_days": 2,
    },

    # Hudson - onboarding
    {
        "title": "Watch a Roblox Studio intro tutorial (~2 hrs)",
        "outcome": "You can open Studio, navigate the Explorer panel, insert a Part, run a test session, and publish a place. You don't need to write code — you need to recognize the UI.",
        "acceptance": "Comment a 1-sentence note: 'I can open Studio and X' (where X is something concrete you did).",
        "category": "meta",
        "assignee": "Hudson",
        "priority": "high",
        "due_offset_days": 1,
    },
    {
        "title": "Decide your specialization: research or building?",
        "outcome": "Pick one: trend research (TikTok/YouTube scanning, IP vetting, concept generation) OR building (directing Claude via Studio MCP to make game systems). You can swap later, but pick a primary now so we can assign concrete work.",
        "acceptance": "Reply in this task's comments with your pick + why.",
        "category": "meta",
        "assignee": "Hudson",
        "priority": "medium",
        "due_offset_days": 2,
    },
]

def main():
    conn = psycopg2.connect(
        f"postgresql://postgres:{DB_PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres?sslmode=require",
        connect_timeout=10,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Get team_member IDs
    cur.execute("select id, name from public.team_members")
    member_by_name = {name: id for id, name in cur.fetchall()}

    inserted = 0
    skipped = 0
    for t in TASKS:
        assignee_id = member_by_name.get(t["assignee"])
        if not assignee_id:
            print(f"  SKIP: no team_member for {t['assignee']}")
            continue

        # Idempotency: skip if same title + assignee already exists
        cur.execute("""
            select id from public.tasks
            where title = %s and assignee_id = %s
        """, (t["title"], assignee_id))
        if cur.fetchone():
            print(f"  exists: [{t['assignee']}] {t['title']}")
            skipped += 1
            continue

        cur.execute("""
            insert into public.tasks
              (title, outcome, acceptance, category, assignee_id, priority,
               due_date, status)
            values
              (%s, %s, %s, %s, %s, %s,
               current_date + (%s || ' days')::interval, 'todo')
            returning id
        """, (
            t["title"], t["outcome"], t["acceptance"], t["category"],
            assignee_id, t["priority"], t["due_offset_days"],
        ))
        task_id = cur.fetchone()[0]
        cur.execute("""
            insert into public.activity (actor_id, verb, target_type, target_id, summary)
            values (%s, 'created', 'task', %s, %s)
        """, (assignee_id, task_id, f"Task created for {t['assignee']}: {t['title']}"))
        print(f"  inserted: [{t['assignee']}] {t['title']}")
        inserted += 1

    cur.close()
    conn.close()
    print(f"\n✓ {inserted} inserted, {skipped} already existed")

if __name__ == "__main__":
    main()
