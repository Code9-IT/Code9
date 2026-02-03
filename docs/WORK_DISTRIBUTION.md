# Work Distribution Guide

The repo is intentionally split so that **four people can work in
parallel** with almost no merge conflicts.  Each person "owns" a
directory.  Shared files (`docker-compose.yml`, `.env.example`,
`db/init/001_init.sql`) should be changed via a feature branch + PR.

---

## Suggested ownership

| Area | Files / directories | What to build next |
|------|---------------------|--------------------|
| **Database & Generator** | `db/`, `services/generator/` | Richer anomaly patterns, data-freshness checks, maybe a second init script for seed data |
| **Agent & Prompt** | `services/agent/routes/`, `services/agent/llm/` | Real Ollama integration, prompt tuning, action-parsing from LLM output |
| **RAG & Knowledge** | `services/agent/rag/` | Choose + integrate a vector store, ingest sample maritime docs |
| **Grafana & UI** | `grafana/` | Polish panels, add the "Analyze" button/link in the Events table, colour-code severity |
| **DevOps & Docs** | `docker-compose.yml`, `docs/`, `scripts/`, `README.md` | CI/CD, Ollama setup script, expand architecture docs |

---

## Rules to keep merge conflicts low

1. **Own your directory.** Don't touch someone else's files without a
   quick chat (or a PR).
2. **Use feature branches** – never push directly to `master`.
3. **`db/init/001_init.sql`** is shared – discuss schema changes before
   you commit; open a PR so everyone sees the diff.
4. **Search for `TODO`** in the codebase to find pre-marked items.
   Each one is intentionally left for someone to pick up.

---

## Finding work

```bash
# List every TODO in the repo
grep -r "TODO" --include="*.py" --include="*.yml" --include="*.sql" --include="*.md" .
```

Pick one, create a branch, implement, open a PR.
