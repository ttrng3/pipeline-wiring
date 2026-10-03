# Spec: preview-wrapper

**Approved:** 2026-10-04

**Intent:** accepted 2026-10-04 · **Status:** approved

## Requirements
1. `tools/preview_matches.py <saved preview> <build>` removes exactly the publisher's skeleton, then requires the rest to equal the build byte for byte; JSON out, exit 0 only on a match. (Outcome)
2. The skeleton head must hash to one of the two pinned known heads; the tail `\n</body></html>` must be exact. (Outcome; open question 1, chosen: pin both)
3. Step 4 of `verification/wiring.md` uses it, and the hash comparison of `index.html` goes. (Outcome)
4. It passes against the preview titled "Pipeline Wiring" today. (Outcome)

## Design
- **`tools/preview_matches.py`:** gdsh-report's script (2026-10-02), with one change. `SKELETON_HEAD_SHA256` becomes `KNOWN_HEADS`, a set of two:
  - `65aeed0fe57327ab5aa05983225a4a29182a3b56007728748fc02df09a0df9b3`: the 537-byte head, the same one gdsh pinned;
  - `e31337138497e60f14bd7cf04bac72f75eec8a64666fcbee2b21afb15bc08f02`: the 355-byte head on a preview republished 2026-10-03.

  The JSON reports which one matched (`skeleton_head`: its byte length).
- **Step 4 of `verification/wiring.md`:** `Artifact read` the preview's `index.html` into the session's scratch folder under a neutral name. Then run `python3 tools/preview_matches.py <saved> <build>`, where the build is a fresh `tools/build-fragment.py` output from `main` (or from `$c` via `git archive`). Expected: exit 0, `"match": true`. The data-file hash comparisons stay as they are.
- **Evidence:** the script's JSON, in place of the raw `index.html` hash. **Traps:** the skeleton note, as in gdsh.
- **`tools/verify_live.py`:** add `tools/preview_matches.py` to `PRIVATE`, so it must exist on `main` and answer 404.

## Conflicts
Loaded earlier today in this session and still current: kernel `standing-instructions.md`, root `CLAUDE.md`, the artifact mirror contract, entity separation, the repo's `CLAUDE.md` and `REVIEW.md`, secure-pages.

| Rule (by name) | What in the design touches it | Resolution |
|---|---|---|
| Artifact mirror contract | Step 4 reads the preview | Read-only, found by title; the saved copy stays in the session's scratch folder, outside the repo; no id or URL written |
| Never by value (REVIEW.md) | Two hashes written into the repo | They hash the publisher's generic skeleton, which holds no id, URL or personal data |
| Changes reach `main` through a PR and Ty's ship | One new script, protocol edits | One PR, reviewed, then the ship phrase; not during the routine's run |

None needs Ty's call.

## Security
```
## Security (secure-pages, 2026-10-04)
1 Secrets ........ PASS | history: 0 hits (re-run for this spec)
2 Visibility ..... PUBLIC — PASS (unchanged; ruled earlier today)
3 Pages .......... PASS: tools/ is outside the watched data/ area; the new file is not served, and verify_live.py now checks its 404
4 Supabase ....... N/A
Verdict: safe to ship
```

## Promise
On the branch, then on `main` after merge: `python3 tools/preview_matches.py <saved preview index.html> <build>` prints `"match": true` and exits 0 against the preview titled "Pipeline Wiring". A preview with one byte changed in the fragment, and one with an unknown skeleton head, each exit 1. Step 1 still passes. Measured 2026-10-04.

## Out of scope
Any change to the preview, the routine, the page or the data; the other repos' step 4.
