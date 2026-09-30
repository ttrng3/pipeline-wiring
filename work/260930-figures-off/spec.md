# Spec

Status: approved by Ty 30/09 ("approve 6", in chat).

- `index.html`, section 7, three notes lose their figures and keep their meaning:
  - Trade Journal schedule note: the 26/09 manual run "brought the new fills in" (no fill count, no running total).
  - ECOPM "corrected 25/09" note: "W02 and W03 backfilled, and W01 rebuilt" (no per-week row counts, before or after).
  - ECOPM detail-file note: the defect hit "most rows", and the fix still owed is for "the older weeks" (no row counts or week counts).
- Whole-page scan (30/09, every number on the page, not only the removed ones) for other pipeline figures, amounts, business-record counts or people's names found none left in `index.html` after review round 1. Counts of repos, artifacts, previews, API list rows and the knowledge graph's size are system status, not a pipeline's data, and stay.
- `starter-story.html` and `learning-matrix.html` are not edited (one writer each, CLAUDE.md); hits there are reported in the PR, not changed.
- The figures remain in git history; rewriting it is Ty's call (CLAUDE.md).
- Promise: `git diff c849d87 -- index.html` changes only these three notes, none of the removed figures appears anywhere in the tree (checked with the figures passed at run time, never written to a file), and the next Pages run is green and serves the page with the same nine rows.
