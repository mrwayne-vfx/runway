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

-- Public summary the friends page reads: one row per team, written by the team app every ~30 s.
create table if not exists public.runway_public (
  team text primary key,
  leg integer, leg_name text, runner text,
  lat double precision, lng double precision, src text,
  km_done double precision, km_total double precision,
  eta_finish timestamptz, race_start timestamptz,
  started boolean default false, finished boolean default false,
  at timestamptz not null default now()
);
alter table public.runway_public enable row level security;
create policy "public anon read"   on public.runway_public for select to anon using (true);
create policy "public anon insert" on public.runway_public for insert to anon with check (true);
create policy "public anon update" on public.runway_public for update to anon using (true) with check (true);
alter publication supabase_realtime add table public.runway_public;

-- Cheers from the friends page: insert-only from the browser, readable by everyone.
create table if not exists public.runway_cheers (
  id bigint generated always as identity primary key,
  team text not null,
  emoji text not null,
  name text,
  at timestamptz not null default now()
);
create index if not exists runway_cheers_team_at on public.runway_cheers (team, at desc);
alter table public.runway_cheers enable row level security;
create policy "cheers anon read"   on public.runway_cheers for select to anon using (true);
create policy "cheers anon insert" on public.runway_cheers for insert to anon with check (char_length(emoji) <= 8 and (name is null or char_length(name) <= 24));
alter publication supabase_realtime add table public.runway_cheers;
-- The Runway tracker: run once in the Supabase SQL editor AFTER supabase-setup.sql.
-- Adds the cheer message and the leg record the friends page reads.
alter table public.runway_cheers add column if not exists msg text;
drop policy if exists "cheers anon insert" on public.runway_cheers;
create policy "cheers anon insert" on public.runway_cheers for insert to anon
  with check (char_length(emoji) <= 8 and (name is null or char_length(name) <= 24) and (msg is null or char_length(msg) <= 80));
alter table public.runway_public add column if not exists along_km double precision;
alter table public.runway_public add column if not exists next_runner text;
alter table public.runway_public add column if not exists exchange_eta timestamptz;
alter table public.runway_public add column if not exists legs jsonb;

-- Rehearsal mode removes its pretend bike when it ends.
drop policy if exists "pos anon delete" on public.runway_pos;
create policy "pos anon delete" on public.runway_pos for delete to anon using (true);

-- Lets the team app clear test cheers before race day.
drop policy if exists "cheers anon delete" on public.runway_cheers;
create policy "cheers anon delete" on public.runway_cheers for delete to anon using (true);
