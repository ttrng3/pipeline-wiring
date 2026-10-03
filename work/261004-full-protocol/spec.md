# Spec: full-protocol

**Approved:** 2026-10-04

**Intent:** accepted 2026-10-04 · **Status:** approved

## Requirements
1. `verification/wiring.md` and `tools/verify_live.py` on `main`, in the shape of the 7 pipeline protocols. (Intent, Outcome)
2. Step 1 is one script that exits 0 only when every verdict is true, printing one JSON object. (Outcome)
3. The 4 allowlisted files match `main`, and the private files answer 404. (Outcome, first bullet)
4. `data/status.json` parses, its summary agrees with its rows, and every row has a state. (Outcome, second bullet)
5. The page's heartbeat is no older than 26 hours. (Outcome, third bullet)
6. `test_bands.py` prints ALL PASS. (Outcome, fourth bullet)
7. No preview id, trigger id, personal trace or forbidden word in any served or tracked file. (Outcome, fifth bullet)
8. A browser step (three tabs, every live cell filled, no console error) and a preview step (the fragment plus three companions). (Outcome)
9. `learning-matrix.html` is checked only for being served and equal to `main`; its content stays with its routine. (Open question 1, chosen yes)
10. Passes once on the live site after merge, and is drilled with at least one deliberate breakage. (Outcome)

## Design
Two new files and nothing else. No change to the page, the two tab files, `collect_status.py`, `bands.yaml`, the workflows, the routines or `.pages-allow`. `verification/` and `tools/` are outside the watched `data/` area, so Pages won't serve them.

**`tools/verify_live.py`** is modelled on `Omni-TMDV/tools/verify_live.py`. Verdicts:

| Verdict | Check |
|---|---|
| `served_equals_main` | `index.html`, `starter-story.html`, `learning-matrix.html` and `data/status.json` return 200 with the sha256 of `main` |
| `private_not_served` | README, CLAUDE.md, REVIEW.md, `bands.yaml`, `data/.last-check`, the three `tools/` files plus this one, `verification/wiring.md`, `.pages-allow`, one `work/` file and (when present) one `triage/` file found at run time all exist on `main` and answer 404 |
| `status_consistent` | `summary.pipelines` equals the row count; `summary.fresh` equals the rows with `fresh: true`; every row has `key`, `band` and `preview.state` |
| `rows_match_collector` | the row keys equal the keys of `PIPELINES` in `tools/collect_status.py`, in order |
| `page_has_every_cell` | `index.html` holds one `data-next`, `data-hb` and `data-preview` cell per row key |
| `heartbeat_fresh` | first field of `data/.last-check` ≤ 26 h (the on-call's limit, `on-call.yml`) |
| `status_fresh` | `generatedUtc` ≤ 26 h |
| `bands_tests_pass` | `python3 tools/test_bands.py` exits 0 and prints ALL PASS |
| `all_tracked_read` | every tracked text file was read |
| `no_personal_traces` | no storage link, email address, bare handle, or `trig_` trigger id in any served or tracked file |
| `no_forbidden_words` | none of the `--forbid` words in any served or tracked file; fails if none are given |

`--forbid` takes the nine preview ids and any person's handle. The runner reads them at run time from the status routine's prompt and its own notes, and they are never written to the repo. A 22-character artifact id has no shape a regex can tell from ordinary text, which is why the ids are passed in rather than pattern-matched.

**`verification/wiring.md`:**
- **Step 1:** the script.
- **Step 2:** Chrome on the live page. Three tab buttons; after the `status.json` fetch, every `[data-next]`, `[data-hb]` and `[data-preview]` cell differs from its hand-written placeholder. The live `data-hb` cell must hold a date, not `—`, and each `data-preview` pill must carry a state class. Both iframes load with a non-empty body.
- **Step 3:** console errors.
- **Step 4:** the preview, found by title through `Artifact list`. It holds `index.html` equal to a fresh `tools/build-fragment.py` output, plus `starter-story.html`, `learning-matrix.html` and `data/status.json`, each equal to `main` or the last routine commit's copy.
- **Drill:** in a scratch copy, drop one row from `status.json`, and separately add a `trig_` line to a doc. `status_consistent` and `no_personal_traces` must each turn false; nothing is committed.

## Conflicts
Loaded: kernel `standing-instructions.md` and root `CLAUDE.md` (Read tool), the artifact mirror contract and entity-separation memories, the repo's `CLAUDE.md` and `REVIEW.md`, and secure-pages. ty-report-standard and apple-design don't apply: no page changes.

| Rule (by name) | What in the design touches it | Resolution, or question for Ty |
|---|---|---|
| Artifact mirror contract | Step 4 reads the preview | Read-only, found by title; no id or URL written; nothing published or deleted |
| Artifact mirror contract: the publish rule (CLAUDE.md "never the page alone") | Step 4 checks the preview holds all four files | The protocol enforces this rule; it never publishes |
| Each page has one writer (CLAUDE.md Layout) | The script runs `test_bands.py` | `test_bands.py` writes nothing in the repo (CLAUDE.md Commands); the protocol only reads |
| Never add a preview id or trigger id (CLAUDE.md Rules) | The script needs the ids to search for them | Passed at run time; matches printed as count and file only |
| Entity separation | This page lists both entities' repos by name, by design | No entity word check here; `--forbid` carries ids and handles only. The ECP × ELA and EcoPM protocols guard their own repos |
| Changes reach `main` through a PR and Ty's ship (CLAUDE.md) | Two new files | One PR, the reviewer first, then the ship phrase; not merged 15:30–16:30 UTC (the daily run) |

## Security
```
## Security (secure-pages, 2026-10-04)
1 Secrets ........ PASS | history: 0 hits
2 Visibility ..... PUBLIC — PASS: status only (heartbeats, stamps, schedules, preview states); no figures
3 Pages .......... PASS: Actions deploy from main /, allowlist live; README, CLAUDE.md, REVIEW.md, bands.yaml, tools/, data/.last-check, .pages-allow, a work/ file all 404 (curl, 2026-10-04)
4 Supabase ....... N/A: no Supabase
Verdict: safe to ship
```

## Promise
After merge, from a clean `main`, outside the daily run: `python3 tools/verify_live.py --forbid <ids and handles>` prints `"pass": true` and exits 0, and steps 2–4 pass. Measured by 2026-10-05, 12:00 Hanoi. Each drill turns its verdict false. Evidence (the JSON, screenshots, preview hashes) goes in the PR.

## Out of scope
- Whether each pipeline's own row is healthy: that is the page's job, not its protocol's.
- `learning-matrix.html` content.
- Any change to the routines, workflows, collector or page.
- The README "Publishing" drift REVIEW.md mentions.

## Changes during the build
Found in review rounds on PR #18, after approval. The approved text above stands as Ty approved it; Ty's ship phrase accepts these too.
1. `page_has_every_cell` also fails on a cell with no row (a dropped pipeline's stale cells).
2. Step 2 compares each date cell with the date `status.json` holds, so a placeholder can't pass.
3. `--forbid` words are searched in every served and tracked file, this protocol included; only the script is left out of the trace check.
4. A failed `git ls-files` or a non-UTF-8 tracked file can't pass silently.
5. Step 4 names the preview's title, accepts a fragment built from the last routine commit, and posts names and hashes only.
