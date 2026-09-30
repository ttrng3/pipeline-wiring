# Spec

Status: approved by Ty 30/09 ("approve 6", in chat).

- `index.html`, section 7, three notes lose their figures and keep their meaning:
  - Trade Journal schedule note: the 26/09 manual run "brought the new fills in" (no fill count, no running total).
  - ECOPM "corrected 25/09" note: "W02 and W03 backfilled" (no per-week row counts).
  - ECOPM detail-file note: the defect hit "most rows, in every week built before then" (no row counts or week count).
- Whole-page scan (30/09) for other pipeline figures, amounts, business-record counts or people's names found none left in `index.html`. Counts of repos, artifacts, previews, API list rows and the knowledge graph's size are system status, not a pipeline's data, and stay.
- `starter-story.html` and `learning-matrix.html` are not edited (one writer each, CLAUDE.md); hits there are reported in the PR, not changed.
- The figures remain in git history; rewriting it is Ty's call (CLAUDE.md).
- Promise: `git grep -nE '23,577|83 fills|172 rows|175 rows|3,413|5,440' -- index.html` prints nothing at head, and the next Pages run is green and serves the page with the same nine rows.
