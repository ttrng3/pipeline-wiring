# Spec: backup-missed-month-check

**Intent:** accepted 2026-10-03 · **Status:** draft

## Requirements

1. **`--backup` flag.** `tools/collect_status.py` takes `--backup STATE[:note]`, with `STATE` one of `ok | missing | not-due | not-checked`. Like `--preview`, it is used after the collector has run and refuses to run without `data/status.json`. It records
   `"backup": {"name": "Trade Journal Drive backup", "month": "<YYYY-MM>", "state": …, "note": …, "checkedAt": …}`
   in `data/status.json` and adds `"backup": "<state>"` to `summary` (intent, Outcome).
2. **Triage file on `missing`.** It writes `triage/<yymmdd>-trade-journal-backup-missing/intent.md`, unless a folder with that suffix already exists from the same month (`yymm` prefix). So one missing month is one file, and that file is the on-call email. Status only: the month, the expected file name, the folder name, and "the check only reports". It prints `triage written: <path>`, which the routine already commits (intent, Outcome).
3. **No triage file** for `ok`, `not-due` or `not-checked`. A Drive connector failure is `not-checked` and is never reported as missing (intent, Outcome).
4. **Routine prompt, new step 2b**, between the preview check and the commit. The step, by day of the month (UTC):
   - **Days 1–3:** `--backup not-due`.
   - **From day 4:** use the Google Drive connector, read-only, to search for the exact name `trade-journal-backup-<YYYY-MM>-01.json.gz`. Then check that the match's parent folder is named `Backups`.
     - Found there → `--backup ok`.
     - Not found → `--backup missing:"none in Backups on <date>"`.
     - A connector error → `--backup not-checked:"<error>"`.

   The routine never writes to Drive. The prompt is changed only from a same-turn `get` of the live config (intent, Constraints).
5. **Page, section 5.** The sentence "Nothing watches the job itself…" becomes: "From the 4th of each month the daily check looks for the master in `Backups/` and, if it is missing, files a triage note, which emails Ty" (intent, Who and what).

## Design

- **`tools/collect_status.py`:** about 30 lines.
  - an `--backup` argparse option;
  - the record, the summary key, and a `write_backup_triage(month, note, now)` beside `write_triage`;
  - the `--backup` branch shares the "load existing `status.json`" path with `--preview`, so a single call can carry both.
- **`tools/test_bands.py`:** four new offline cases:
  - `ok` writes no file;
  - `missing` writes one file;
  - a second `missing` the same month writes none;
  - `not-checked` writes none and is not reported as missing.

  The script must still print ALL PASS.
- **`index.html`:** the one sentence in section 5.
- **Routine `trig_01LBNQNgvDEWZNg8KkuiR3rU`:**
  - after the merge, `get` it, insert step 2b into its prompt text and `update` it with that body only;
  - step 3's write list already includes new triage files;
  - step 5's report gains "backup: <state>".
- **Not changed:** the on-call workflow, the Trade-Journal repo and the Mac job.

## Conflicts

Policy loaded this session:
- kernel "Standing Instructions" and root `CLAUDE.md`;
- the repo `CLAUDE.md`;
- memories "artifact-mirror-contract", "routine-update-live-config-only" and "pipeline-wiring-ninth";
- secure-pages, below.

The apple-design skill doesn't apply: the only page change is one prose sentence.

| Rule (by name) | What in the design touches it | Resolution |
|---|---|---|
| "The page carries status only … never a pipeline's own figures" (repo `CLAUDE.md`) | `status.json` gains a backup record. | It holds the state, month and file name only; no size, fill count or Drive id. |
| "Never add … a person's details … to this public repo" (repo `CLAUDE.md`) | The routine searches Drive. | Search by file name; no Drive id or account path is written to the repo. Any id stays in the private prompt. |
| "Each page has one writer: the daily check writes only `data/status.json`, `data/.last-check` and new `triage/…/intent.md`" (repo `CLAUDE.md`) | A new triage file kind. | It is still a new `triage/*/intent.md`, which is within the routine's allowed writes. The on-call `paths: ['triage/**']` already covers it. |
| "Routine Updates Use the Live Config" (memory) | The prompt changes. | `get` then `update` in the same turn, inserting only step 2b and the report clause. |
| "The cron table in `PIPELINES` is a second copy of every schedule" (repo Known mistakes) | — | No schedule changes; `PIPELINES` is untouched. |
| Mirror rule (repo `CLAUDE.md` Commands) | `index.html` changes. | Post-merge: rebuild the preview with all three companion files, never the page alone. |
| Entity separation | The page is "OMNI side", but this entry is about a personal pipeline. | The page already lists Trade Journal as one of the nine pipelines; status only, no personal figures. |

## Security (secure-pages, 2026-10-03)

```
1 Secrets ........ PASS (run on the branch before the PR)
2 Visibility ..... PUBLIC — PASS (status only, no new data kind)
3 Pages .......... PASS — .pages-allow unchanged; data/status.json already served
4 Supabase ....... N/A
Verdict: safe to ship
```

## Promise

1. **Offline tests.** `python3 tools/test_bands.py` prints ALL PASS, including the four new backup cases.
2. **Privacy.** `git grep -n -i -E 'gmail\.com|GoogleDrive-[a-z]'` gives no output. The status file carries no Drive id.
3. **Live.** After the merge and the routine update, the next daily run (16:00 UTC) reports `backup: ok` for October, since the master is in `Backups/`. `data/status.json` at that commit has `"backup": {"state": "ok", "month": "2026-10", …}`. Measured on the first run after the merge.

## Out of scope

- Watching other Mac jobs, such as the knowledge graph.
- Checking the CSV moves or file sizes.
- Changing the Mac job.
- A page cell for the backup state. The status line and the email are enough; add one later if wanted.
