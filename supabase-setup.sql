-- The Runway tracker: shared team state. Run once in the Supabase SQL editor.
create table if not exists public.runway_state (
  team text primary key,
  data jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.runway_state enable row level security;
-- The app uses the anon key; anyone with the key + team code can read and write. Keep both out of public posts.
create policy "runway anon read"   on public.runway_state for select to anon using (true);
create policy "runway anon insert" on public.runway_state for insert to anon with check (true);
create policy "runway anon update" on public.runway_state for update to anon using (true) with check (true);
-- Realtime so the other phone sees changes as they happen.
alter publication supabase_realtime add table public.runway_state;

-- Live positions: one row per phone that opts in to "Share this phone's position".
create table if not exists public.runway_pos (
  device text primary key,
  team text not null,
  label text,
  kind text,
  runner_id text,
  lat double precision,
  lng double precision,
  acc integer,
  speed double precision,
  at timestamptz not null default now()
);
alter table public.runway_pos enable row level security;
create policy "pos anon read"   on public.runway_pos for select to anon using (true);
create policy "pos anon insert" on public.runway_pos for insert to anon with check (true);
create policy "pos anon update" on public.runway_pos for update to anon using (true) with check (true);
alter publication supabase_realtime add table public.runway_pos;
