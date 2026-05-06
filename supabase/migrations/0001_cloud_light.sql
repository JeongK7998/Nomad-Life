-- Nomad Life cloud-light schema.
-- Supabase is a queue/snapshot layer, not the Hermes runtime.

create extension if not exists pgcrypto;

create table if not exists public.capture_queue (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  source text not null default 'dashboard',
  status text not null default 'pending' check (status in ('pending', 'processing', 'processed', 'failed', 'ignored')),
  payload jsonb not null,
  processed_at timestamptz,
  local_capture_id text,
  error text
);

create table if not exists public.workout_queue (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  source text not null default 'workout_quick',
  status text not null default 'pending' check (status in ('pending', 'processing', 'processed', 'failed', 'ignored')),
  payload jsonb not null,
  processed_at timestamptz,
  local_workout_session_id text,
  error text
);

create table if not exists public.dashboard_snapshots (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  snapshot_key text not null,
  snapshot_date date,
  schema_version text not null default '0.1.0',
  payload jsonb not null,
  source text not null default 'mac_hermes_worker'
);

create index if not exists capture_queue_status_created_idx
  on public.capture_queue (status, created_at);

create index if not exists workout_queue_status_created_idx
  on public.workout_queue (status, created_at);

create index if not exists dashboard_snapshots_key_created_idx
  on public.dashboard_snapshots (snapshot_key, created_at desc);

create table if not exists public.sync_logs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  worker text not null,
  action text not null,
  target_table text,
  target_id uuid,
  status text not null,
  details jsonb not null default '{}'::jsonb
);

alter table public.capture_queue enable row level security;
alter table public.workout_queue enable row level security;
alter table public.dashboard_snapshots enable row level security;
alter table public.sync_logs enable row level security;

-- Browser clients may only enqueue new pending records.
-- Processing, failure marking, and local id writes are service-role only.
drop policy if exists "anon_insert_capture_queue" on public.capture_queue;
create policy "anon_insert_capture_queue"
  on public.capture_queue
  for insert
  to anon
  with check (
    status = 'pending'
    and source in ('dashboard', 'capture_quick', 'workout_quick')
    and processed_at is null
    and local_capture_id is null
    and error is null
  );

drop policy if exists "anon_insert_workout_queue" on public.workout_queue;
create policy "anon_insert_workout_queue"
  on public.workout_queue
  for insert
  to anon
  with check (
    status = 'pending'
    and source in ('dashboard', 'workout_quick')
    and processed_at is null
    and local_workout_session_id is null
    and error is null
  );

-- Hosted Dashboard can read derived display snapshots.
-- Do not publish raw Notes, Calendar, HealthKit, finance ledgers, or private files here.
drop policy if exists "anon_read_dashboard_snapshots" on public.dashboard_snapshots;
create policy "anon_read_dashboard_snapshots"
  on public.dashboard_snapshots
  for select
  to anon
  using (true);
