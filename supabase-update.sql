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
