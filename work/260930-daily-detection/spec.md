# Spec

Status: approved by Ty 30/09 ("Approve the 4 specs but skip Teams", in chat). Builds on `work/260930-preview-ids-out/` (same script; this branch starts from that one).

## Repo
- `bands.yaml` (new, not published): two thresholds in JSON syntax, which is valid YAML, so no PyYAML is needed in the cloud: `lateGraceHours` 2, `missedAfterHours` 24.
- `tools/collect_status.py`: each pipeline gets a band, written into its `data/status.json` row (`band`, `bandKind`, `bandReason`) and summarised as `summary.logOnly` / `summary.diagnose`.
  - **diagnose / stale:** heartbeat older than the pipeline's watchdog (`maxHeartbeatAgeDays`, already in the script).
  - **diagnose / missed-run:** the latest scheduled fire (from the cron table) has no heartbeat after it, more than 24 h later.
  - **log / late:** the same, but under 24 h. **log / unreadable:** the heartbeat file could not be fetched (a network blip must not open a triage item).
  - A diagnose finding writes `triage/<yymmdd>-<key>-<kind>/intent.md`: names, times, cron and thresholds only; never the heartbeat note or any pipeline's data. If a folder for the same key and kind already exists, nothing is written, so an open item is not duplicated daily. Ty closes one by deleting its folder in a PR.
  - The cron table's own row moves to `0 16 * * *`. `next_fire` and a new `prev_fire` share one cron matcher.
- `tools/test_bands.py` (new): offline check with planted heartbeats in a temp folder.
- `.pages-allow`: `!bands.yaml`. `triage/` gets no line: it is outside every watched area so it is never published, and a `!` glob would fail the Pages run while the folder is empty. Ty's approval of this spec is the say-so for these two new kinds of file.
- Docs: README layout rows, CLAUDE.md (writes + test command), REVIEW.md one-writer line, the page's own schedule cell, diagram line and script comment.

## Routine (applied at ship, not before)
The cron move belongs with the ship: before the merge, the old script would compare against a weekly row and the prompt would name files that don't exist. At ship, one `update` built from a same-turn `get`, byte-checked after:
- cron `0 16 * * 0` → `0 16 * * *` (23:00 Hanoi daily; on Sundays still after TMDV 11:00 and ECP × ELA 14:00 UTC).
- "YOUR ONLY WRITES ARE `data/status.json` AND `data/.last-check`." → also "any new `triage/<yymmdd>-<key>-<kind>/intent.md` the script reports as `triage written:`; create only, never edit or delete one".
- Step 3 commits those new triage files after the two data files.
- Step 5's one-line report also requires no pipeline in the log or diagnose band; otherwise a fifth line lists diagnose pipelines with their reasons and log ones by name.
- CADENCE: daily 16:00 UTC.
No Teams, no other routine, no act tier.

## Promise
1. `python3 tools/test_bands.py` prints ALL PASS: a clean day gives nine `ok` bands and no triage file; one planted stale heartbeat gives exactly one `triage/*/intent.md`, and a second run adds none; a missed run is diagnose, the same run inside 24 h is log only.
2. A live local run against the nine repos (data files restored after) writes no triage file today.
3. After the ship, the routine's first daily run commits `data/status.json` with a `band` on every row.
