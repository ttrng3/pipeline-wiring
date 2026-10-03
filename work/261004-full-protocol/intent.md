# Intent: one full verification protocol for the Pipeline Wiring page

**Status:** accepted 2026-10-04
**Source:** chat, 2026-10-04 (Ty's Gate 3 ruling: "let ECPxELA and pipeline wiring have a full protocol")

**Problem.** Gate 3 of the build loop asks for one full protocol per pipeline. The 7 shipped 1–2 Oct each prove the whole live page with `verification/<page>.md` plus `tools/verify_live.py`. This repo has none: no `verification/` folder, only `tools/test_bands.py` for the detection tiers. Nothing re-runnable proves that https://ttrng3.github.io/pipeline-wiring/ serves the right files and that its live cells are filled. Ty ruled on 2026-10-04 that Gate 3 passes only when this repo and ecp-ela-weekly have one.

**Outcome.** `verification/wiring.md` and `tools/verify_live.py` exist on `main`, in the same shape as the 7. Step 1 is a script that exits 0 with every verdict true:
- the 4 allowlisted files are byte-identical to `main`, and the private files answer 404 (README, CLAUDE.md, REVIEW.md, `tools/`, `bands.yaml`, `triage/`, `work/`, the heartbeat);
- `data/status.json` parses, its summary count matches, and every pipeline row has a state;
- the page's own heartbeat is no older than the on-call's 26 hours;
- `test_bands.py` prints ALL PASS;
- no preview id, trigger id, personal trace or forbidden word appears in any served or tracked file.

A browser step loads all three tabs, fills every live cell and shows no console error. A preview step checks that the Cowork preview holds the page fragment plus its three companion files, matching `main` or the last run. The protocol passes once against the live site after merge, and is drilled with at least one deliberate breakage.

**Who and what is affected.** The `pipeline-wiring` repo only, plus one Progress line in the AI-Native Build Loop doc. The daily status routine, the Learning Matrix routine, the on-call workflow and the page itself don't change.

**Constraints.**
- The page carries status only, never a pipeline's figures (CLAUDE.md Rules).
- Never write a preview id, trigger id, person's details or secret into the repo; the forbidden words are passed at run time.
- Each file keeps its one writer: the protocol only reads.
- Don't merge during the daily 23:00 Hanoi run.
- Changes reach `main` only through a PR and Ty's ship phrase.

**Open questions.**
1. `learning-matrix.html` is rewritten monthly by its own routine. Should the protocol check only that it is served and equal to `main`, and leave its content to that routine? I recommend yes. **Chosen: yes** (Ty accepted with the recommendations, 2026-10-04).
