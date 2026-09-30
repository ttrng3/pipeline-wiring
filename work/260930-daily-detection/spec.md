# Spec

Status: approved by Ty 30/09 ("Approve the 4 specs but skip Teams", in chat). Builds on `work/260930-preview-ids-out/` (same script; this branch starts from that one).

## Repo
- `bands.yaml` (new, not published): two thresholds in JSON syntax, which is valid YAML, so no PyYAML is needed in the cloud: `lateGraceHours` 2, `missedAfterHours` 24.
- `tools/collect_status.py`: each pipeline gets a band, written into its `data/status.json` row (`band`, `bandKind`, `bandReason`) and summarised as `summary.logOnly` / `summary.diagnose`.
  - **diagnose / stale:** heartbeat older than the pipeline's watchdog (`maxHeartbeatAgeDays`, already in the script).
  - **diagnose / missed-run:** the first scheduled run after the heartbeat (from the cron table) is more than 24 h in the past.
  - **log / late:** that run is more than 2 h but at most 24 h in the past. **log / unreadable:** a network error, HTTP 429 or a 5xx fetching the heartbeat (a blip must not open a triage item). **diagnose / no-heartbeat:** any other HTTP error such as 404, or a timestamp that does not parse.
  - If `bands.yaml` does not parse (say a YAML-style hand edit), the run prints a warning and uses 2 h / 24 h instead of failing.
  - This page reads its own heartbeat from yesterday's run, so a daily run that starts more than 2 h after 16:00 shows itself as log/late for that day. That is harmless (log writes no file) and accepted.
  - A diagnose finding writes `triage/<yymmdd>-<key>-<kind>/intent.md`: names, times, cron and thresholds only; never the heartbeat note or any pipeline's data. While any triage folder for the same pipeline is open, nothing more is written for it, so one outage (missed run, then stale) is one item, not one a day. The written paths are printed (`triage written: …`), not stored in the published `data/status.json`. Ty closes one by deleting its folder in a PR.
  - The cron table's own row moves to `0 16 * * *`. `next_fire` and a new `prev_fire` share one cron matcher.
- `tools/test_bands.py` (new): offline check with planted heartbeats in a temp folder.
- `.pages-allow`: its "Writers:" comment says daily; no line changes. `bands.yaml` (repo root) and `triage/` are outside every watched area (`@data/` is the only one), so Pages never serves them and no line is needed; a `!` glob would fail the run while `triage/` is empty. They are still readable in the public repo, so triage files carry status only.
- Docs: README layout rows, CLAUDE.md (writes + test command), REVIEW.md one-writer line, the page's own schedule cell, diagram line and script comment.

## Routine (applied at ship, not before)
The cron move belongs with the ship, **in the same turn as the merge, right after it**: before the merge the old script would compare against a weekly row and the prompt would name files that don't exist; after it, a Sunday run on merged code with the old weekly cron would disagree with the table (the drift in CLAUDE.md's known mistakes). The ship turn, in order: (1) if the routine's last heartbeat on main is more than 20 h old, fire it once on the current main and wait for it, so the first daily run does not read the old weekly gap as a missed run of its own (review round 3); (2) merge; (3) one `update` built from a same-turn `get`, byte-checked after; (4) fire it once and check the run shows Pipeline Wiring `ok` or `log` and writes no triage file. The `update`:
- cron `0 16 * * 0` → `0 16 * * *` (23:00 Hanoi daily; on Sundays still after TMDV 11:00 and ECP × ELA 14:00 UTC).
- "YOUR ONLY WRITES ARE `data/status.json` AND `data/.last-check`." → also "any new `triage/<yymmdd>-<key>-<kind>/intent.md` the script reports as `triage written:`; create only, never edit or delete one".
- Step 3 commits those new triage files after the two data files.
- Step 5's one-line report also requires no pipeline in the log or diagnose band; otherwise a fifth line lists diagnose pipelines with their reasons and log ones by name.
- CADENCE: daily 16:00 UTC.
No Teams, no other routine, no act tier.

## Promise
1. `python3 tools/test_bands.py` prints ALL PASS: a clean day gives nine `ok` bands and no triage file; one planted stale heartbeat gives exactly one `triage/*/intent.md`, and a second run adds none; a missed run is diagnose for a weekly and a daily pipeline, the same run inside 24 h is log only; this page's own daily run is `ok` at start delays of 0–40 min and diagnose when a day is missing; a pipeline with an open item gets no second one; a network error is log with no file, a 404 is diagnose with one.
2. A live local run against the nine repos (data files restored after) writes no triage file today.
3. After the ship, the routine's first daily run commits `data/status.json` with a `band` on every row.
