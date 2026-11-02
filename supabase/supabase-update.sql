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

-- Photos from the road: the team app uploads to a public storage bucket and files a row here; the friends page reads both.
insert into storage.buckets (id, name, public) values ('runway', 'runway', true) on conflict (id) do nothing;
drop policy if exists "runway photos read"   on storage.objects; create policy "runway photos read"   on storage.objects for select to anon using (bucket_id = 'runway');
drop policy if exists "runway photos upload" on storage.objects; create policy "runway photos upload" on storage.objects for insert to anon with check (bucket_id = 'runway');
drop policy if exists "runway photos delete" on storage.objects; create policy "runway photos delete" on storage.objects for delete to anon using (bucket_id = 'runway');
create table if not exists public.runway_photos (
  id bigint generated always as identity primary key,
  team text not null, path text not null, url text not null,
  leg integer, by text, caption text, w integer, h integer,
  at timestamptz not null default now()
);
create index if not exists runway_photos_team_at on public.runway_photos (team, at desc);
alter table public.runway_photos enable row level security;
drop policy if exists "photos anon read"   on public.runway_photos; create policy "photos anon read"   on public.runway_photos for select to anon using (true);
drop policy if exists "photos anon insert" on public.runway_photos; create policy "photos anon insert" on public.runway_photos for insert to anon with check (caption is null or char_length(caption) <= 120);
drop policy if exists "photos anon delete" on public.runway_photos; create policy "photos anon delete" on public.runway_photos for delete to anon using (true);
alter publication supabase_realtime add table public.runway_photos;

-- The Runway tracker: lets the team app wipe everything for a fresh test ("Reset the whole team" in Setup).
drop policy if exists "runway anon delete" on public.runway_state;  create policy "runway anon delete" on public.runway_state  for delete to anon using (true);
drop policy if exists "public anon delete" on public.runway_public; create policy "public anon delete" on public.runway_public for delete to anon using (true);
