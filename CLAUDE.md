# Working on The Runway tracker

The repository is the single source of truth. Edit only files under `src/`; never edit built output.

## Workflow
1. `git pull --rebase` before starting: a collaborator may have pushed.
2. Edit `src/app.html` (crew tracker), `src/follow.html` (friends page), or the data files in `src/`.
3. Build and check locally: `python3 src/build.py`, then serve `src/dist` (`cd src/dist && python3 -m http.server 8765`) and test in a browser at phone width (390 px), in both day and night skins.
4. Commit with a clear message and push to `main`. GitHub Actions (`.github/workflows/pages.yml`) runs `src/build.py` and deploys `src/dist` to GitHub Pages in about a minute. A failed build deploys nothing.
5. If `main` is protected and the push is refused, push a branch and open a pull request for the owner to approve.
6. Confirm the run in the Actions tab (`gh run list --limit 1`).

## Rules
- Anything on the live team (`runway2026`) is seen by friends on shiftandplay.com. Test on the test team: add `?test=1` to crew and friends links.
- Bump the service worker cache name in `src/build.py` (`runway-vNN`) when changing the crew app, so installed phones pick it up.
- Database changes go in a new file under `supabase/`, run by the owner in the Supabase SQL Editor. Don't rely on deletes through the public key on the live team (the lockdown script blocks them).
- Keep each page self-contained: fonts, logos, data and the map library are inlined at build time so the pages work offline.
- The race is Nov 4 to 7, 2026. From Nov 2, fixes only on `main`; anything new goes through a pull request.
