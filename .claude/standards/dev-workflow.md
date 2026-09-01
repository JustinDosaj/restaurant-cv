# Development Workflow

How a change travels from an idea to production: branching, schema migrations, tests, and deploys. The environment pipeline itself (Railway/Neon/CI design) is specced in issue #68; this doc is the day-to-day driver's manual.

## The databases

| Database | Lives | Schema is updated by | When |
| --- | --- | --- | --- |
| **Dev** | Neon (our account) | `npm run db:migrate` (local `DATABASE_URL` points here permanently) | You, whenever you generate a migration |
| **Test** | Local Postgres 16 — Docker Compose on your machine (`docker compose up -d`), a service container in CI | Dropped and rebuilt from scratch at the start of every `npm run test:integration` (reset → migrate → seed lookups) | Automatic on every integration test run |
| **Staging** | Neon (our account) | Railway pre-deploy `db:migrate` on every deploy of `main` | Automatic on merge to `main` |
| **Production** | Neon (Replit-provisioned) — until DNS cutover | `npm run db:migrate` run manually against its URL | You, immediately after a schema change merges to `main` |

After cutover, production moves to a Railway environment tracking the `production` branch and migrates itself on deploy, same as staging.

## Everyday workflow (no schema changes)

1. Start from updated `main`: `git switch main && git pull`
2. Branch: `git switch -c <type>/<name>` (`feat/…`, `fix/…`, `performance/…`)
3. Build; keep `npm run check` and `npm run test` green
4. Push, open a PR into `main`
5. Merge → staging redeploys `main` automatically

## Workflow with schema changes

1. Branch off updated `main` as above
2. Edit the schema in `database/schemas/`
3. `npm run db:generate` — creates the migration file in `database/drizzle/` (commit it with the feature)
4. `npm run db:migrate` — applies it to the dev database
5. Build and test as normal — `npm run test:integration` syncs the test database itself before running, so there is nothing extra to remember. (`npm run db:migrate:test` exists for syncing the test DB without running tests.)
6. PR; merge
7. Staging updates itself: the Railway pre-deploy step runs the migration before the new code goes live — a failed migration fails the deploy and the old version keeps serving
8. **Interim manual step:** point `DATABASE_URL` at the Replit production database and run `npm run db:migrate`, then point it back at dev. Do this promptly after every schema-change merge so prod never drifts from `main`

Optional, for genuinely risky or destructive schema work: create a temporary Neon branch of the dev database and point `DATABASE_URL` at it while iterating. This is an escape hatch, not a routine step — normal work happens directly against dev.

## Promotion to production (post-cutover)

Production tracks a fast-forward-only `production` pointer branch. No PRs, no merges into it:

```
git push origin main:production
```

That one deliberate push deploys the Railway production environment, which migrates its database pre-deploy exactly like staging. Rollback is moving the pointer back to an earlier commit. `git log production` always answers "what is production running."

## Command reference

| Command | What it does |
| --- | --- |
| `npm run db:generate` | Generate a migration file from schema changes — the only way schema changes may reach a shared database |
| `npm run db:migrate` | Apply pending migrations to `DATABASE_URL`. Journal-tracked: re-running with nothing new is a free no-op |
| `npm run db:migrate:test` | Same, against `TEST_DATABASE_URL` (from the test env file). Called automatically by `test:integration` after `scripts/reset-test-db.ts` has dropped the schema — so the test DB always carries exactly the current branch's migrations, and switching between branches with divergent migrations needs no manual cleanup. Refuses to run if the URL matches `DATABASE_URL` |
| `npm run db:push` | **Local prototyping only.** Never against test, staging, or production — those change only via migration files |

## Rules

- **Merged migration files are immutable.** Once a migration is on `main` it has run somewhere; never edit or delete it. Got it wrong? Write a new migration that fixes it forward.
- **One schema change, one migration, same PR.** The migration file ships in the same PR as the code that needs it, so code and schema arrive together in every environment.
- **The test database is nobody's working database.** Integration tests seed and delete data, and `test:integration` drops the whole `public` schema first. The vitest config, `drizzle.test.config.ts`, and the reset script all refuse to run when `TEST_DATABASE_URL` matches `DATABASE_URL`, and the reset only ever drops on a loopback host (`localhost` / `127.0.0.1`) — a remote URL is skipped with a log line. Don't work around either guard.
- **Tests run on plain Postgres, production on Neon.** `database/client.ts` selects the `node-postgres` driver under `NODE_ENV=test` and `neon-http` otherwise. The one meaningful driver difference is interactive transactions, which the codebase deliberately never uses — keep it that way, or the test driver stops proving anything about production.
- **A brand-new empty database is initialized with `npm run db:migrate`** (the baseline migration builds the full schema). The historical stamp procedure (marking the 2026-07 re-baseline as already applied on then-existing databases) was a one-time event — never needed for new databases.

## Interim status (delete sections as they land)

- Staging auto-migrate activates when PR #133 (`railway.json`) merges; CI-gated deploys arrive with the #72 dashboard wiring.
- Replit is the real production until DNS cutover; the manual prod migrate in step 8 above is the discipline that keeps it at zero drift.
- The migration drift CI check (schema change without a generated migration fails the PR) is issue #70.
