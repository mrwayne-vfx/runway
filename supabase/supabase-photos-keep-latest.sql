-- The Runway: clear the old test photos from the live friends page, keeping only the most recent one.
-- Run once in the Supabase SQL Editor. The image files stay in storage; only the gallery entries are removed.

-- 1. Look first: the photo that will be kept (the newest on the live team).
select id, at, by, caption, url from public.runway_photos where team = 'runway2026' order by at desc limit 1;

-- 2. Remove every other live photo entry.
delete from public.runway_photos
where team = 'runway2026'
  and id <> (select id from public.runway_photos where team = 'runway2026' order by at desc limit 1);

-- 3. Check: should show 1.
select count(*) as live_photos from public.runway_photos where team = 'runway2026';
