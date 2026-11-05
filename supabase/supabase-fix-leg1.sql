-- RACE NIGHT FIX: keep only the leg 1 start on the live team (runway2026); remove any later legs started by mistake.
-- Leg 1 keeps the time it was recorded (or 9:00 PM if none). Runner tags, tracker phone, cheers and photos are untouched.
-- Run once in the Supabase SQL Editor.
update public.runway_state
set data = (data - 'actual' - 'manualNow' - 'stamps' - 'epoch')
        || jsonb_build_object(
             'epoch', (extract(epoch from now()) * 1000)::bigint,
             'actual', jsonb_build_object('1', coalesce(data->'actual'->>'1', '2026-11-04T21:00')),
             'manualNow', null,
             'device', 'sql-fix-leg1',
             'stamps', coalesce((select jsonb_object_agg(key, value) from jsonb_each(data->'stamps')
                                 where key not like 'actual.%' and key <> 'manualNow'), '{}'::jsonb)
                       || (select jsonb_object_agg('actual.'||n, to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')) from generate_series(1,67) n)
                       || jsonb_build_object('manualNow', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'))),
    updated_at = now()
where team = 'runway2026';

-- Check: recorded_starts should show only leg 1.
select data->'actual' as recorded_starts, data->>'raceStart' as race_start from public.runway_state where team = 'runway2026';
