# Spec

Status: approved by Ty 30/09 ("approve", in chat).

- `tools/collect_status.py` stops copying the note: no `heartbeatNote` key on any row, including the fetch-failure case. Nothing reads the note; bands use the fetch status and the timestamp, so no band changes.
- `index.html` drops the hover line that showed the note. Heartbeat date, age, fresh/stale pill, bands and preview pills stay.
- The committed `data/status.json` loses the key now, so the public file is clean before the next run.
- No filtering or rewording of notes: deciding which free text is safe would be guesswork. The source repos' own `data/.last-check` notes are a separate change (routine prompts), not this PR.
- Old values stay in git history; rewriting it is Ty's call and not part of this spec.

## Promise
1. `grep -c heartbeatNote data/status.json tools/collect_status.py index.html` prints 0 for each.
2. `python3 tools/test_bands.py` prints ALL PASS.
3. A live local run against the nine repos (data files restored after) writes 9 rows with no `heartbeatNote` key and none of the note text.
4. The page script, run under node on the committed `data/status.json`, draws 9 heartbeat cells and 9 preview pills, and sets no hover title on a heartbeat cell.
