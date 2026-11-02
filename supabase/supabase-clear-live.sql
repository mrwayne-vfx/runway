-- Clear race progress on the LIVE team (runway2026) before race day.
-- Keeps runner tags and cheers. Removes recorded starts, positions, test photos and the friends summary,
-- puts the race start back to Wed Nov 4 9:00 PM, and bumps the reset marker so every crew phone drops its old starts.
update public.runway_state
set data = jsonb_build_object(
      'epoch', (extract(epoch from now()) * 1000)::bigint,
      'raceStart', '2026-11-04T21:00',
      'startSet', true,
      'manualNow', null,
      'actual', '{}'::jsonb,
      'assign', coalesce(data->'assign', '{}'::jsonb),
      'runners', coalesce(data->'runners', '[]'::jsonb),
      'device', 'sql-reset',
      'stamps', coalesce((select jsonb_object_agg(key, value) from jsonb_each(data->'stamps') where key like 'assign.%'), '{}'::jsonb)
                || jsonb_build_object('raceStart', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                                      'manualNow', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'))
    ),
    updated_at = now()
where team = 'runway2026';
delete from public.runway_public where team = 'runway2026';
delete from public.runway_pos    where team = 'runway2026';
delete from public.runway_photos where team = 'runway2026';
