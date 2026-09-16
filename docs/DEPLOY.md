# Deploying (free tier)

Two independent deploys: the API to **Render** (using `Dockerfile.api`, already in this
repo), the UI to **Vercel**. Do the API first — the UI needs its URL.

## 1. Push first

Everything in this doc assumes `master` is pushed to GitHub and the repo is connected
to your account — both Render and Vercel deploy by pulling from GitHub.

## 2. API → Render

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. **New +** → **Web Service** → connect the `football-data-explorations` repo.
3. Configure:
   - **Name:** `football-data-api` (or anything)
   - **Region:** whichever is closest to you
   - **Branch:** `master`
   - **Root Directory:** leave blank (repo root)
   - **Runtime:** Docker
   - **Dockerfile Path:** `Dockerfile.api`
   - **Instance Type:** Free
4. **Create Web Service** and wait for the build (a few minutes on the free tier).
5. Once live, copy the URL, e.g. `https://football-data-api.onrender.com`.
6. Sanity check: open `https://<your-url>/api/health` — should return `{"status":"ok"}`.

**Free-tier note:** the service spins down after ~15 minutes idle. The first request
after that takes 30–50 seconds to wake up — expected, not a bug. Worth a one-line
mention in the README/demo so it doesn't look broken to someone clicking in cold.

## 3. UI → Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. **Add New...** → **Project** → import the same repo.
3. In the configure screen: **Root Directory** → **Edit** → select `app/web`.
4. Framework Preset: Next.js (auto-detected).
5. **Environment Variables** → add:
   - `NEXT_PUBLIC_API_URL` = the Render URL from step 2 (no trailing slash)
6. **Deploy.**
7. Copy the resulting URL, e.g. `https://football-data-explorations.vercel.app`.

`NEXT_PUBLIC_API_URL` is read at **build time** (it's a client-side env var), so if you
ever change the API URL, redeploy the Vercel project rather than just restarting it.

## 4. Confirm CORS

`app/api/main.py` already allows any `https://*.vercel.app` origin (see the
`allow_origin_regex` in `CORSMiddleware`), so this should just work. If a chart image
fails to load on the deployed UI, open the browser console — a CORS error there means
the Vercel domain doesn't match that pattern (e.g. a custom domain), and
`allow_origin_regex`/`allow_origins` needs updating to match.

## 5. Wire the URL back into the README

Once both are live, replace the "Live demo" placeholder line in the root `README.md`
with the actual Vercel URL, and flip the GitHub repo to **Public** (Settings → General
→ Danger Zone → Change visibility).
