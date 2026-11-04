-- The Runway, race day: clear any leg starts recorded before the gun on the LIVE team (runway2026).
-- Keeps runner tags, cheers and photos. Puts the gun back to Wed Nov 4 9:00 PM, clears the leg override,
-- and bumps the reset marker so every crew phone drops the stray starts it has saved.
-- Run once in the Supabase SQL Editor.

-- 1. Look first (send this result to Claude if anything looks odd): what's recorded now.
select data->'raceStart' as race_start, data->'manualNow' as leg_override, data->'actual' as recorded_starts,
       data->'tracker' as tracker_phone, data->>'device' as last_phone_to_save,
       (select jsonb_object_agg(key, value) from jsonb_each(data->'stamps') where key like 'actual.%' or key in ('raceStart','manualNow')) as when_saved
from public.runway_state where team = 'runway2026';

-- 2. Clear the starts.
update public.runway_state
set data = (data - 'actual' - 'manualNow' - 'raceStart' - 'startSet' - 'epoch' - 'stamps' - 'tracker')
        || jsonb_build_object(
             'epoch', (extract(epoch from now()) * 1000)::bigint,
             'raceStart', '2026-11-04T21:00',
             'startSet', true,
             'manualNow', null,
             'actual', '{}'::jsonb,
             'device', 'sql-race-day-reset',
             'stamps', coalesce((select jsonb_object_agg(key, value) from jsonb_each(data->'stamps')
                                 where key not like 'actual.%' and key not in ('raceStart','manualNow','startSet','tracker')), '{}'::jsonb)
                       || jsonb_build_object('raceStart', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                                             'manualNow', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                                             'tracker',   to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'))),
    updated_at = now()
where team = 'runway2026';

-- 3. Clear the friends summary and stale positions (the countdown comes back). Photos and cheers stay.
delete from public.runway_public where team = 'runway2026';
delete from public.runway_pos    where team = 'runway2026';

-- 4. Check: race_start 2026-11-04T21:00, no recorded starts, assignments still there.
select data->>'raceStart' as race_start, data->'actual' as recorded_starts,
       (select count(*) from jsonb_object_keys(data->'assign')) as legs_assigned
from public.runway_state where team = 'runway2026';
