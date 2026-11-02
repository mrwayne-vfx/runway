-- The Runway: tighten the database before race day. Run once in the Supabase SQL Editor.
-- The live team (runway2026) can no longer have anything deleted through the public key;
-- the test team (runway2026-test) keeps its resets. Crew can still record starts, tag runners and delete a bad photo.
-- (The SQL Editor itself is unaffected: you can always clean up from there.)

drop policy if exists "runway anon delete" on public.runway_state;
create policy "runway anon delete" on public.runway_state for delete to anon using (team like '%-test');

drop policy if exists "public anon delete" on public.runway_public;
create policy "public anon delete" on public.runway_public for delete to anon using (team like '%-test');

drop policy if exists "pos anon delete" on public.runway_pos;
create policy "pos anon delete" on public.runway_pos for delete to anon using (team like '%-test');

drop policy if exists "cheers anon delete" on public.runway_cheers;
create policy "cheers anon delete" on public.runway_cheers for delete to anon using (team like '%-test');

-- cheers only for our two teams, with the existing length limits
drop policy if exists "cheers anon insert" on public.runway_cheers;
create policy "cheers anon insert" on public.runway_cheers for insert to anon
  with check (team in ('runway2026','runway2026-test') and char_length(emoji) <= 8
              and (name is null or char_length(name) <= 24) and (msg is null or char_length(msg) <= 80));

-- positions, state and the summary only for our two teams
drop policy if exists "pos anon insert" on public.runway_pos;
create policy "pos anon insert" on public.runway_pos for insert to anon with check (team in ('runway2026','runway2026-test'));
drop policy if exists "runway anon insert" on public.runway_state;
create policy "runway anon insert" on public.runway_state for insert to anon with check (team in ('runway2026','runway2026-test'));
drop policy if exists "public anon insert" on public.runway_public;
create policy "public anon insert" on public.runway_public for insert to anon with check (team in ('runway2026','runway2026-test'));
