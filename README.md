# roblox-snapshots

Hourly public-data snapshots of new Roblox games, collected by GitHub Actions.

Everything here comes from Roblox's public, unauthenticated endpoints (current players, visits, favorites, votes, chart positions). The repository is public so its scheduled Actions run without consuming a private-repo minute quota. Do not put anything else here: no keys, no site data, no evaluations, no business decisions. Those live in the private ops repository.

## What runs

`.github/workflows/snapshot.yml`, every hour at :17 UTC (and on manual dispatch):

1. `discover`: read Roblox chart sorts (Top Trending, Up and Coming, ...) for candidate universe IDs.
2. `scripts/select_ids.py`: chart IDs plus previously tracked IDs, minus `data/exclude.txt`, keeping only games created within the last 60 days. A game seen for the first time gets one snapshot; if it turns out to be older, it drops out.
3. `snapshot`: append one row per tracked game to `data/history/<universeId>.jsonl`.
4. Once per UTC day, `rank` writes `reports/daily/YYYY-MM-DD.md` and `data/candidates/latest.json`.
5. Commit and push the changes.

The scripts come from the private skills repository (`my-roblox-game-discovery`), checked out with the read-only secret `SKILLS_READ_TOKEN`.

## Data

| Path | Content |
|---|---|
| `data/history/<universeId>.jsonl` | One snapshot per line, append-only. Same format as `roblox-hit-evaluator`'s `HISTORY_JSONL`, so a file can be passed to `evaluate.py derive` directly |
| `data/tracked.txt` | Universe IDs snapshotted hourly |
| `data/exclude.txt` | Universe IDs never snapshotted (edit by hand) |
| `data/discover/latest.json` | Latest chart read |
| `data/candidates/latest.json` | Latest daily ranking |
| `data/errors/YYYY-MM.jsonl` | Failed requests; failures are never written as zeros |
| `reports/daily/YYYY-MM-DD.md` | Daily "new and rising" list |

All times are UTC. Missing hours are gaps, not zeros, and cannot be backfilled later.

## Maintenance

- `SKILLS_READ_TOKEN` is a fine-grained PAT limited to read-only Contents on the skills repository. Renew it before it expires, or every run fails at checkout.
- GitHub disables scheduled workflows after 60 days without repository activity. The hourly commits should count as activity; if the workflow ever shows as disabled, re-enable it under Actions.
- The history grows by roughly 1–1.5 MB per day. Archive a year at a time if the repository gets large.
