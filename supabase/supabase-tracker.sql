-- The Runway: background tracking. OwnTracks (free, iOS and Android) posts the phone's position here with the screen off.
-- Two endpoints, one per team, so test runs never touch the live page. Run once in the Supabase SQL Editor.
create or replace function public._runway_ot(team_code text, p jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if coalesce(p->>'_type','') <> 'location' or p->>'lat' is null or p->>'lon' is null then return '[]'::jsonb; end if;
  insert into public.runway_pos (device, team, label, kind, runner_id, lat, lng, acc, speed, at)
  values ('ot-' || coalesce(nullif(p->>'tid',''),'xx'), team_code, 'Tracker', 'bike', null,
          (p->>'lat')::double precision, (p->>'lon')::double precision,
          nullif(p->>'acc','')::integer,
          case when p ? 'vel' then (p->>'vel')::double precision / 3.6 else null end,
          coalesce(to_timestamp((p->>'tst')::double precision), now()))
  on conflict (device) do update set team = excluded.team, lat = excluded.lat, lng = excluded.lng, acc = excluded.acc,
    speed = excluded.speed, at = excluded.at, kind = 'bike'
  where public.runway_pos.at <= excluded.at;
  return '[]'::jsonb;
end $$;
create or replace function public.owntracks(jsonb) returns jsonb language sql security definer set search_path = public as $$ select public._runway_ot('runway2026', $1) $$;
create or replace function public.owntracks_test(jsonb) returns jsonb language sql security definer set search_path = public as $$ select public._runway_ot('runway2026-test', $1) $$;
revoke all on function public._runway_ot(text, jsonb) from public, anon, authenticated;
grant execute on function public.owntracks(jsonb) to anon;
grant execute on function public.owntracks_test(jsonb) to anon;
