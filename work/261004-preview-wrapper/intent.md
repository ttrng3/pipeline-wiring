# Intent: step 4 compares the preview with the publisher's wrapper removed

**Status:** accepted 2026-10-04
**Source:** chat, 2026-10-04 (Ty: "fix step 4 first, then worktrees"), after the post-merge run on PR #18

**Problem.** Step 4 of `verification/wiring.md` compares the preview's `index.html` hash with the built fragment. The publishing service wraps every published page in its own document skeleton (`<!doctype html>` … `<body>` and `</body></html>`), so the raw hashes can never be equal, even when the preview is correct. Found 2026-10-04 on the post-merge run of #18: raw hashes differed; with the wrapper removed, the preview equalled the build byte for byte. gdsh-report hit the same defect and fixed it on 2026-10-02 (#13, `tools/preview_matches.py`). The skeleton is not fixed: two versions were seen on 2026-10-04 (537 bytes, the one gdsh pinned; 355 bytes on a preview republished 2026-10-03).

**Outcome.** `tools/preview_matches.py <saved preview> <build>` exists in this repo, modelled on gdsh's. It removes exactly the publisher's skeleton: the head must hash to one of the pinned known heads, and the tail must be exact. Then the rest must equal the build byte for byte. It prints JSON and exits 0 only on a match. Step 4 of `verification/wiring.md` uses it, and it passes against the preview titled "Pipeline Wiring" today.

**Who and what is affected.** This repo's `verification/wiring.md` (step 4, Evidence, Traps) and one new `tools/` file. No change to the page, data, routines or the preview.

**Constraints.** The protocol only reads the preview; nothing is published. No preview id or URL is written. Changes reach `main` through a PR and Ty's ship phrase.

**Open questions.**
1. Should the script accept both skeletons seen today (pinned by hash), so a republish with either passes? I recommend yes. **Chosen: yes, pin both** (Ty, 2026-10-04). A new skeleton still fails until it is pinned on purpose.
