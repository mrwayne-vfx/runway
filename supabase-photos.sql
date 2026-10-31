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
