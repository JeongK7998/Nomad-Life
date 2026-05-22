-- Require Supabase Auth for hosted Nomad Life data.
-- Browser clients use the anon key plus a persisted user session.

alter table public.capture_queue
  add column if not exists user_id uuid references auth.users(id) on delete set null;

alter table public.workout_queue
  add column if not exists user_id uuid references auth.users(id) on delete set null;

alter table public.dashboard_snapshots
  add column if not exists user_id uuid references auth.users(id) on delete set null;

alter table public.sync_logs
  add column if not exists user_id uuid references auth.users(id) on delete set null;

create index if not exists capture_queue_user_status_created_idx
  on public.capture_queue (user_id, status, created_at);

create index if not exists workout_queue_user_status_created_idx
  on public.workout_queue (user_id, status, created_at);

create index if not exists dashboard_snapshots_user_key_created_idx
  on public.dashboard_snapshots (user_id, snapshot_key, created_at desc);

drop policy if exists "anon_insert_capture_queue" on public.capture_queue;
drop policy if exists "anon_insert_workout_queue" on public.workout_queue;
drop policy if exists "anon_read_dashboard_snapshots" on public.dashboard_snapshots;

drop policy if exists "authenticated_insert_capture_queue" on public.capture_queue;
create policy "authenticated_insert_capture_queue"
  on public.capture_queue
  for insert
  to authenticated
  with check (
    user_id = auth.uid()
    and status = 'pending'
    and source in (
      'dashboard',
      'capture_quick',
      'workout_quick',
      'exercise_library_manager',
      'workout_quick_library_manager'
    )
    and processed_at is null
    and local_capture_id is null
    and error is null
  );

drop policy if exists "authenticated_read_own_capture_queue" on public.capture_queue;
create policy "authenticated_read_own_capture_queue"
  on public.capture_queue
  for select
  to authenticated
  using (user_id = auth.uid());

drop policy if exists "authenticated_insert_workout_queue" on public.workout_queue;
create policy "authenticated_insert_workout_queue"
  on public.workout_queue
  for insert
  to authenticated
  with check (
    user_id = auth.uid()
    and status = 'pending'
    and source in ('dashboard', 'workout_quick')
    and processed_at is null
    and local_workout_session_id is null
    and error is null
  );

drop policy if exists "authenticated_read_own_workout_queue" on public.workout_queue;
create policy "authenticated_read_own_workout_queue"
  on public.workout_queue
  for select
  to authenticated
  using (user_id = auth.uid());

-- Snapshots are sanitized display data, but hosted clients still read only
-- snapshots published for the same Supabase Auth user.
drop policy if exists "authenticated_read_dashboard_snapshots" on public.dashboard_snapshots;
create policy "authenticated_read_dashboard_snapshots"
  on public.dashboard_snapshots
  for select
  to authenticated
  using (user_id = auth.uid());

drop policy if exists "authenticated_read_sync_logs" on public.sync_logs;
create policy "authenticated_read_sync_logs"
  on public.sync_logs
  for select
  to authenticated
  using (user_id = auth.uid());
