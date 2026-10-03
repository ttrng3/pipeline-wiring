# Verification: the wiring page

## Promise

Every file https://ttrng3.github.io/pipeline-wiring/ serves (the page, its two tab files, `data/status.json`) is byte-identical to `main`, and every other tracked file answers 404. `data/status.json` agrees with itself, with the collector's `PIPELINES` table and with the page's live cells. The daily check ran within the on-call's 26 hours, and the band tests pass. No preview id, trigger id, email address, handle or storage link sits in any served or tracked file. In the browser the three tabs load, every live cell is filled and nothing errors. The Cowork preview holds the page fragment and its three companion files, matching `main` or the last daily run.

## Clean state

```bash
cd ~/Projects/pipeline-wiring && git checkout main && git pull --ff-only
```
Run any time except during the daily check (16:00 UTC = 23:00 Hanoi, `0 16 * * *` in `tools/collect_status.py`), and after any merge once its Pages run is green (`gh run list -w "Pages (allowlist)" -L1`).

## Steps

1. **Repo and live site.** `python3 tools/verify_live.py --forbid <words>` → exit 0 and `"pass": true`. The words are the nine preview ids, read at run time from the status routine's prompt (`RemoteTrigger get` on the daily check's routine), plus any person's handle the runner knows has leaked anywhere before. Never write them here. Without `--forbid`, `no_forbidden_words` fails on purpose.
2. **Live page in Chrome.** Open https://ttrng3.github.io/pipeline-wiring/ and run the script under Invariants. Expected: all values true.
3. **Console.** Reload, then read errors for `TypeError|ReferenceError|Uncaught|SyntaxError`. Expected: none.
4. **Preview.** Find the preview by its title with `Artifact list` (the runner may not have `RemoteTrigger get`; never write its id here). `Artifact list` its files, and `Artifact read` `index.html` and `data/status.json`. Expected: exactly `index.html`, `starter-story.html`, `learning-matrix.html` and `data/status.json` (CLAUDE.md: never the page alone). `index.html` has the sha256 of a fresh `python3 tools/build-fragment.py` output (`build/artifact.html`). Each other file read has the sha256 of `main`'s copy, or of the last routine commit's copy: `c=$(git log --first-parent --format='%h %s' -- data/status.json | /usr/bin/grep -v ' (#[0-9]*)$' | head -1 | cut -d' ' -f1)`, then `git show $c:<path> | shasum -a 256`. Matching `$c` and not `main` means PRs changed the file since the run: behind by design until the next run.

## Invariants

Step 1 prints these verdicts, all of which must be true:
- `served_equals_main`
- `private_not_served`
- `status_consistent`
- `rows_match_collector`
- `page_has_every_cell`
- `heartbeat_fresh` (≤ 26 h, `on-call.yml`)
- `status_fresh` (≤ 26 h)
- `bands_tests_pass`
- `all_tracked_read`
- `no_personal_traces`
- `no_forbidden_words`

Step 2, in the page:
```js
window.confirm=()=>true; window.alert=()=>{};
await new Promise(r=>setTimeout(r,3000));
const st=await fetch('data/status.json?v='+Date.now()).then(r=>r.json());
const cells=a=>st.pipelines.map(p=>document.querySelector(`[${a}="${p.key}"]`));
const dm=/^\d\d\/\d\d/;
const frameOk=async t=>{const f=document.querySelector(`iframe[src="${t}"]`); if(!f) return false;
  const r=await fetch(t+'?v='+Date.now()); return r.ok && (await r.text()).length>1000;};
JSON.stringify({three_tabs:document.querySelectorAll('[role=tab]').length===3,
  status_loaded:!/not loaded/.test(document.getElementById('status-when').textContent),
  next_filled:cells('data-next').every(c=>c&&dm.test(c.textContent.trim())),
  hb_filled:cells('data-hb').every(c=>c&&c.querySelector('.pill')),
  preview_filled:cells('data-preview').every(c=>c&&c.querySelector('.pill:not(.p-mute)')),
  starter_frame:await frameOk('starter-story.html'), learning_frame:await frameOk('learning-matrix.html')})
```
All of them must be true. `preview_filled` is false while a preview's state is "not checked"; that is a real finding for the daily check, not a protocol fault.

## Adversary

- **A stranger on the public page.** `private_not_served`: README, CLAUDE.md, REVIEW.md, `bands.yaml`, the heartbeat, the four `tools/` scripts, this protocol, one `work/` file and one `triage/` file (when any exist), found at run time, all exist on `main` and answer 404. `no_personal_traces` and `no_forbidden_words` keep preview ids, trigger ids and people off every served and tracked file. The ids left the current files on 30/09 (#7); this catches one creeping back.
- **A daily check that stopped.** `heartbeat_fresh`, `status_fresh`. The on-call emails at 26 h; this protocol fails at the same line.
- **A schedule changed in one copy only** (26/09: the "Next" column was wrong). `rows_match_collector` catches a pipeline added or dropped in `PIPELINES` but not in the data. A changed cron alone is not caught (Not covered).
- **A row with no cell, or a cell with no row.** `page_has_every_cell`, and `next_filled` / `hb_filled` / `preview_filled` in the browser.
- **A status file that lies about itself.** `status_consistent`: summary counts against the rows.
- **The detection tiers broken by an edit.** `bands_tests_pass`.
- **A preview published without its companions** (25/09: blank tabs, no error). Step 4.

## Sanctioned substitutes

- Preview ids have no shape a regex can tell from ordinary text, so they are passed with `--forbid` rather than pattern-matched. This proves none of the ids passed is present; it can't catch an id nobody passed. Trigger ids do have a shape (`trig_` + 8 or more characters) and are matched.
- The preview can't be fetched by a script, so step 4 is done by the runner with `Artifact list` and `Artifact read`.

## Evidence

- The JSON from step 1 and the JSON from step 2.
- Screenshots (`save_to_disk: true`): each of the three tabs.
- For step 4: the preview's file list and the hashes read.

## Not covered

- Whether each pipeline is healthy. That is what the page reports; its own rows are checked against the daily check, not re-measured.
- A cron changed in a routine but not in `PIPELINES`. The routine schedules live outside this repo.
- `learning-matrix.html` and `starter-story.html` content (Ty, 04/10: the Learning Matrix belongs to its routine).
- The hand-written prose in sections 2–7.

## Traps

- Pages answers `cache-control: max-age=600`. A `served_equals_main` failure straight after a merge or a daily run is the cache: wait for the Pages run, then re-run.
- The daily run commits `data/status.json` and `.last-check` directly. A run during the check makes live and `main` disagree for a few minutes.
- This page's own heartbeat is read from the remote repo, so its `data-hb` cell shows the previous run's stamp (CLAUDE.md). The cell is still filled.
- On the Mac, `grep` is a wrapper around ugrep; use `/usr/bin/grep` for the step 4 commands.
