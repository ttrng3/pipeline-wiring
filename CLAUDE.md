# CLAUDE.md — pipeline-wiring

The wiring page: every repo, preview and routine, and what is broken. Ty's own infrastructure page, OMNI side. Live: https://ttrng3.github.io/pipeline-wiring/

**If you are a scheduled routine:** each routine follows its own prompt and the files that prompt names (the daily status check's prompt names `tools/collect_status.py` and limits writes to `data/status.json`, `data/.last-check` and new files under `triage/`; the monthly Learning Matrix prompt names `README.md`). Your prompt and those files outrank this file. This file adds no step to a run.

## Commands
- Build the Cowork preview page: `python3 tools/build-fragment.py` (writes `build/artifact.html`). When the routine refreshes the preview is set by its runbook, not here. Never send `index.html` itself to the preview; Pages does serve it.
- Test the bands and the triage folder offline (no network, writes nothing in the repo): `python3 tools/test_bands.py` (must print ALL PASS)
- Check `data/status.json` parses and its summary count matches: `python3 -c "import json;d=json.load(open('data/status.json'));assert d['summary']['pipelines']==len(d['pipelines'])"`

## Layout
- `index.html` is the page (three tabs; its prose is edited by hand). `starter-story.html` and `learning-matrix.html` are tabs 2 and 3, loaded in iframes.
- Each page has one writer: the daily check writes only `data/status.json`, `data/.last-check` and new `triage/<yymmdd>-<key>-<kind>/intent.md` files (never a page); `learning-matrix.html` is rewritten only by the Learning Matrix routine; no routine writes `starter-story.html` (REVIEW.md).
- `.github/workflows/on-call.yml` is the on-call: a red run is the email to Ty. It fails when a push adds a `triage/*/intent.md`, and at 20:00 UTC when the first field of `data/.last-check` is 26h+ old. Its cron and limit copy the daily check's schedule; change them with it.
- `build/` is generated and git-ignored. Never hand-edit or commit it.
- `.pages-allow` lists what Pages publishes; `.github/workflows/pages.yml` deploys only that. Every tracked file under a watched area needs a `.pages-allow` line (published, or `!` for known but not published); a new kind of file needs Ty's say-so and that line in its own PR first.
- `README.md` explains the page and the mirror; `REVIEW.md` holds the reviewer's rules and says where the README is out of date.

## Rules
- Changes reach `main` through a PR and Ty's ship. The only direct writes are the ones a routine's prompt and runbook allow.
- The routine prompts, `README.md` and `REVIEW.md` win over this file and any memory note.
- The page carries status only: heartbeats, stamps, schedules, preview states. Never a pipeline's own figures, and never any entity's business data.
- Never add a Cowork preview URL or artifact id, a trigger id, a person's details or a secret to this public repo. The nine preview ids are kept in the status routine's prompt, which checks the previews; they left the current files on 2026-09-30 (Ty's 29/09 ruling) but remain in git history before that.

## Known mistakes
- The cron table in `PIPELINES` (`tools/collect_status.py`) is a second copy of every schedule; when a routine's cron changed without it, the "Next" column was wrong (2026-09-26).
- `api.github.com` inside a routine answers 403 for every repo except the attached one; it is not a rate limit, and the collector reads only raw.githubusercontent.com (script docstring, 2026-09-26).
- This page's own heartbeat is read from the remote repo, so it shows the previous run's stamp (2026-09-26).
- Publishing `index.html` itself to the preview nests it and renders blank; the tabs and live cells also need the two iframe files and `data/status.json` beside the page (README "Publishing" 2026-09-25, "Layout" 2026-09-26).
- This repo's builder strips document wrappers; other repos' builders cut at `<title>`. They are not interchangeable, and a naive `</?head` regex also eats `<header>` (`tools/build-fragment.py`, 2026-09-25).
- A dead artifact id means "retired", not "missing". The Learning Matrix and Starter Story live only here; a standalone copy was rebuilt by mistake and deleted the same day (README, 2026-09-25).
- The page once said "nothing here is from memory" while carrying stale claims from earlier sessions (2026-09-25).
- Another session had pushed while an edit was in progress; a preview built from an older checkout would have been stale (2026-09-25).
