# Intent: the daily check emails Ty when a month's Trade Journal master never reaches Drive

**Status:** accepted 2026-10-03
**Source:** chat, 2026-10-03

**Problem.** Trade Journal's monthly Drive backup is a Mac job (Trade-Journal #13, 2026-10-03). It alerts Ty when a run fails, but a run that never happens can't alert anyone. If the Mac stays off past the 1st, or the job is unloaded, the month's master just isn't in Drive `09 Trading/Trade Journal/Backups/`, and nobody is told. Section 5 of this page says "Nothing watches the job itself". Review of #15 (2026-10-03) raised it; Ty asked for the check the same day.

**Outcome.** From the 4th of each month, the daily status check (routine, 16:00 UTC) looks in Drive for `trade-journal-backup-<YYYY-MM>-01.json.gz` in that folder.
- **Found:** `data/status.json` records it as ok.
- **Missing:** it writes one `triage/<yymmdd>-trade-journal-backup-missing/intent.md` that month. The existing on-call workflow turns that into an email to Ty.
- **Days 1–3:** recorded as "not due".

A check: a dry run with the file present and with it absent gives "ok" and one triage file. A second dry run gives no second file.

**Who and what is affected.**
- `tools/collect_status.py`: a new `--backup` flag, the status field and the triage file.
- The daily routine's prompt: one new step that uses the Drive connector it already has.
- `index.html` section 5: the "nothing watches" sentence changes.
- Not touched: the Trade-Journal repo, the Mac job and the on-call workflow.

**Constraints.**
- The routine stays read-only on Drive; it only lists or searches.
- The page carries status only: no file sizes, fills or figures.
- No Drive file id, path with the account email, or preview id is written into this public repo. Any id the routine needs stays in its private prompt.
- The routine prompt is updated only from a same-turn `get` of the live config (memory "Routine Updates Use the Live Config").
- Changes reach `main` through a PR and Ty's ship.

**Open questions.**
- None.
