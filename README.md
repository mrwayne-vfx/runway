# The Runway tracker

Live tracking for the Shift & Play team at #RUNTOMTL, the 650 km Toronto to Montréal relay (Nov 4 to 7, 2026, 67 legs).

Two pages:

- **Crew tracker** – https://mrwayne-vfx.github.io/runway/ – for the team: current leg, runner tags, drive times, the RV planner, live position, cheers and photos. Installs to a phone's home screen and works offline.
- **Friends page** – https://mrwayne-vfx.github.io/runway/follow.html – for family and friends: who's running, where the team is, each runner's legs, photos, and cheers back to the crew. Embedded on shiftandplay.com/ultra-relay#track.

## How it's built

Edit the files in `src/`. Every push to `main` runs `src/build.py` on GitHub, which bundles everything into three files and publishes them. If the build fails, nothing is published and the live site stays as it was. Check the **Actions** tab after a push; a deploy takes about a minute.

| File | What it is |
|---|---|
| `src/app.html` | Crew tracker: markup, styles and code in one file |
| `src/follow.html` | Friends page: markup, styles and code in one file |
| `src/data.js` | The 67 legs from the booklet: names, distances, planned times, directions, notes |
| `src/routes.js` | Route geometry per leg: the run line traced from the booklet maps, and the drive line |
| `src/team.js` | The 13 people: names, words, roles and portraits (inline images) |
| `src/sprites.js` | The four animated cheer icons |
| `src/fonts.css` | Big Shoulders Display and Bricolage Grotesque, inlined so they work offline |
| `src/vendor-leaflet.*` | The map library (Leaflet 1.9.4) |
| `src/brand/` | Shift & Play, #RUNTOMTL and Narro logos |
| `src/build.py` | Bundles the above into `src/dist/` (not committed) |
| `supabase/` | Database setup scripts, run in the Supabase SQL Editor |
| `docs/squarespace-embed.html` | The code block pasted into the Squarespace page |
| `tools/routes/` | Scripts and data used to trace the run routes from the booklet PDF (the PDF isn't in the repo) |

Each page shows its build time: the crew tracker in Setup, both pages in their source. When a new version is published, open pages update themselves (the crew tracker shows a "newer version" bar; the friends page reloads quietly unless someone is typing).

## Working on it

1. Edit files in `src/`.
2. Preview locally:
   ```
   python3 src/build.py
   cd src/dist && python3 -m http.server 8000
   ```
   then open http://localhost:8000/ (crew) and http://localhost:8000/follow.html (friends).
3. Commit and push to `main`. Live in about a minute.

For bigger changes, push to a branch and open a pull request, so the other person can look before it goes live.

## Testing without touching the live site

All data is filed under a team code. The live team is `runway2026`; test mode uses `runway2026-test`.

- Crew tracker in test mode: add `?test=1` to any link (e.g. `…/runway/?role=bike&test=1`), or use the switch in Setup. A yellow bar shows it's on. Rehearsal (a pretend bike riding the route) and "Reset the whole team" are only available in test mode.
- Friends page on the test team: `…/runway/follow.html?test=1`.
- Leave test mode with `?test=0` or the same switch.

## Data

Supabase project `sajvndlspknvaquqnakb`. The anon key in the pages is public by design; the table policies decide what it can do.

| Table | What's in it |
|---|---|
| `runway_state` | One row per team: race start, recorded leg starts, runner tags, which phone is the tracker. Merged per key by timestamp. |
| `runway_pos` | One row per phone sharing its position (plus `ot-XX` rows from OwnTracks for background tracking). |
| `runway_public` | The summary the friends page reads, written by crew phones every ~30 s. |
| `runway_cheers` | Cheers and messages from the friends page. |
| `runway_photos` | Photo records; the images live in the `runway` storage bucket. |

Scripts in `supabase/`, in the order they were run: `supabase-setup.sql`, `supabase-update.sql`, `supabase-photos.sql`, `supabase-reset.sql`, `supabase-tracker.sql`. `supabase-clear-live.sql` clears race progress on the live team, keeping tags and cheers.

## Crew roles and links

- Crew: `…/runway/?role=crew`
- SUV driver: `…/runway/?role=suv`
- RV driver: `…/runway/?role=rv`
- Bike support: `…/runway/?role=bike`

The phone that rides with the runner taps **Track this phone** on the Tracker tab. For tracking with the screen off, that phone also runs OwnTracks, set up from the same tab.
