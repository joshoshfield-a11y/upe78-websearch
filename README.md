# UPE78 Metasearch Engine

Actions-dispatchable metasearch over Wikipedia, DuckDuckGo, Hacker News, arXiv, Stack Overflow.
- Run a search: Actions tab -> `search` -> Run workflow -> enter query.
- Every run appends `results/<timestamp>.json` (append-only history) and refreshes `results/latest.json`.
- Frontend: GitHub Pages (`index.html`), auto-deployed by the same workflow.
- API access: trigger via `POST /repos/{owner}/{repo}/actions/workflows/search.yml/dispatches`, read via `results/latest.json` on the default branch.
