# Free Deployment (GitHub Pages + Free Backend)

This app has a React frontend and FastAPI backend.

- Frontend can be hosted free on GitHub Pages (`github.io`).
- Backend cannot run on GitHub Pages because Pages is static-only.

## Option A (recommended): Real app, free

- Frontend: GitHub Pages
- Backend: Render free web service

## 1) Push repo to GitHub

From local repo root:

```bash
git add .
git commit -m "Setup free deployment"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## 2) Enable GitHub Pages deployment

1. Open repo on GitHub.
2. Go to **Settings > Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.

The workflow file already exists:
- `.github/workflows/deploy-frontend-pages.yml`

## 3) Deploy backend for free on Render

1. Create account on Render.
2. New Web Service from your GitHub repo.
3. Root directory: `backend`
4. Build command:

```bash
pip install -r requirements.txt
```

5. Start command:

```bash
PYTHONPATH=. python scripts/ingest_kb.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Add environment variables (optional):
- `OPENAI_API_KEY` (if you want live OpenAI responses)
- `OPENAI_MODEL` (optional, e.g. `gpt-4o-mini`)

After deploy, copy your backend URL, for example:
`https://your-backend.onrender.com/chat`

## 4) Connect frontend to backend URL

1. In GitHub repo, open **Settings > Secrets and variables > Actions > Variables**.
2. Create variable:
- Name: `VITE_API_URL`
- Value: `https://your-backend.onrender.com/chat`

3. Push any commit to `main` or rerun the workflow.

## 5) Your public app link

Your frontend link will be:

`https://<github-username>.github.io/<repo-name>/`

## Option B: GitHub-only static demo

If you do not want any backend host, you can still publish the UI on GitHub Pages, but chat calls to `/chat` will fail because FastAPI is not running.
