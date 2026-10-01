# Spec

Status: approved by Ty 01/10 ("create the paperwork and merge", in chat, after confirming the drill email).

- New `.github/workflows/on-call.yml`. A red run is the alert: GitHub emails the account behind a failed run, and the daily routine pushes as ttrng3. (An issue would not: GitHub never emails you about your own.)
- Push touching `triage/**`: fails when the push adds a `triage/*/intent.md`, naming the folder. Removing a folder does not alert. `collect_status.py` writes one folder per outage, so one email per outage.
- Daily 20:00 UTC: fails when the first field of `data/.last-check` is empty or 26h+ old (the daily check, 16:00 UTC, stopped). These numbers copy the routine's schedule; CLAUDE.md Layout says so.
- Reads only; `permissions: contents: read`. No page, data file or `.pages-allow` change.
- Ty merges, so the scheduled run's failure emails go to his account.
- Promise: the drill on the branch (runs 36807465998, 36807929622) turned both jobs red, and the email "Run failed: On-call - on-call (3a7a9ba)" reached Ty's Gmail at 09:53 Hanoi 01/10 (Ty's screenshot).
