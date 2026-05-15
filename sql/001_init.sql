-- Slingshot — initial schema
-- Run this once via SQL Editor or psycopg2 against the slingshot Supabase project

-- ============ team_members ============
create table if not exists public.team_members (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade unique,
  name text not null,
  role text,
  avatar_initials text,
  avatar_grad text,
  joined_at timestamptz default now()
);

-- ============ games ============
create table if not exists public.games (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  genre text,
  status text not null default 'concept' check (status in ('concept','art','build','qa','live','retired')),
  ships_on date,
  current_ccu int default 0,
  weekly_robux int default 0,
  thumbnail_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============ tasks ============
create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  outcome text,
  acceptance text,
  category text check (category in ('coding','research','admin','creative','approval','design','meta')),
  assignee_id uuid references public.team_members(id) on delete set null,
  created_by uuid references public.team_members(id) on delete set null,
  game_id uuid references public.games(id) on delete set null,
  status text not null default 'todo' check (status in ('todo','in_progress','blocked','in_review','done')),
  priority text not null default 'medium' check (priority in ('low','medium','high','urgent')),
  due_date date,
  external_links jsonb default '[]'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  completed_at timestamptz
);

create index if not exists tasks_assignee_idx on public.tasks(assignee_id);
create index if not exists tasks_status_idx on public.tasks(status);
create index if not exists tasks_due_date_idx on public.tasks(due_date);

-- ============ task_comments (iteration log) ============
create table if not exists public.task_comments (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references public.tasks(id) on delete cascade,
  author_id uuid references public.team_members(id) on delete set null,
  body text not null,
  created_at timestamptz default now()
);

create index if not exists task_comments_task_idx on public.task_comments(task_id);

-- ============ plans (replaces Notion: rubrics/plans/decisions) ============
create table if not exists public.plans (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  kind text not null check (kind in ('plan','rubric','decision','doc')),
  body text,
  created_by uuid references public.team_members(id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============ activity feed ============
create table if not exists public.activity (
  id bigserial primary key,
  actor_id uuid references public.team_members(id) on delete set null,
  verb text not null,
  target_type text,
  target_id uuid,
  summary text,
  created_at timestamptz default now()
);

create index if not exists activity_created_at_idx on public.activity(created_at desc);

-- ============ updated_at trigger helper ============
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists tasks_touch on public.tasks;
create trigger tasks_touch before update on public.tasks
  for each row execute function public.touch_updated_at();

drop trigger if exists games_touch on public.games;
create trigger games_touch before update on public.games
  for each row execute function public.touch_updated_at();

drop trigger if exists plans_touch on public.plans;
create trigger plans_touch before update on public.plans
  for each row execute function public.touch_updated_at();

-- ============ Row Level Security ============
alter table public.team_members enable row level security;
alter table public.tasks enable row level security;
alter table public.task_comments enable row level security;
alter table public.plans enable row level security;
alter table public.activity enable row level security;
alter table public.games enable row level security;

-- Anyone authenticated can read everything (small private team)
drop policy if exists "auth read team_members" on public.team_members;
create policy "auth read team_members" on public.team_members
  for select to authenticated using (true);

drop policy if exists "auth read tasks" on public.tasks;
create policy "auth read tasks" on public.tasks
  for select to authenticated using (true);

drop policy if exists "auth read task_comments" on public.task_comments;
create policy "auth read task_comments" on public.task_comments
  for select to authenticated using (true);

drop policy if exists "auth read plans" on public.plans;
create policy "auth read plans" on public.plans
  for select to authenticated using (true);

drop policy if exists "auth read activity" on public.activity;
create policy "auth read activity" on public.activity
  for select to authenticated using (true);

drop policy if exists "auth read games" on public.games;
create policy "auth read games" on public.games
  for select to authenticated using (true);

-- Authenticated can write
drop policy if exists "auth insert tasks" on public.tasks;
create policy "auth insert tasks" on public.tasks
  for insert to authenticated with check (true);

drop policy if exists "auth update tasks" on public.tasks;
create policy "auth update tasks" on public.tasks
  for update to authenticated using (true);

drop policy if exists "auth delete tasks" on public.tasks;
create policy "auth delete tasks" on public.tasks
  for delete to authenticated using (true);

drop policy if exists "auth insert task_comments" on public.task_comments;
create policy "auth insert task_comments" on public.task_comments
  for insert to authenticated with check (true);

drop policy if exists "auth insert plans" on public.plans;
create policy "auth insert plans" on public.plans
  for insert to authenticated with check (true);

drop policy if exists "auth update plans" on public.plans;
create policy "auth update plans" on public.plans
  for update to authenticated using (true);

drop policy if exists "auth insert games" on public.games;
create policy "auth insert games" on public.games
  for insert to authenticated with check (true);

drop policy if exists "auth update games" on public.games;
create policy "auth update games" on public.games
  for update to authenticated using (true);

drop policy if exists "auth insert activity" on public.activity;
create policy "auth insert activity" on public.activity
  for insert to authenticated with check (true);
