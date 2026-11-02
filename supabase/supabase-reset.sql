-- The Runway tracker: lets the team app wipe everything for a fresh test ("Reset the whole team" in Setup).
drop policy if exists "runway anon delete" on public.runway_state;  create policy "runway anon delete" on public.runway_state  for delete to anon using (true);
drop policy if exists "public anon delete" on public.runway_public; create policy "public anon delete" on public.runway_public for delete to anon using (true);

-- And wipe everything now: starts, tags, positions, the public summary, cheers and photo records (the app's Reset button also removes the photo files; SQL can't).
delete from public.runway_cheers;
delete from public.runway_pos;
delete from public.runway_photos;
delete from public.runway_public;
delete from public.runway_state;
