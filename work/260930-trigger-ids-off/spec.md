# Spec

Status: approved by Ty 30/09 ("approve 5", in chat).

- `index.html`: each `<a href="https://claude.ai/code/routines/trig_…">text</a>` becomes its plain text (15 links; the schedule or routine name they wrapped stays). The deleted Trade Journal routine's id in section 6 is replaced by "had a trigger id that the routine API returns not found for".
- No other tracked file carries a trigger id (whole-tree grep, 30/09). The generic `https://claude.ai/code/routines` list link in README.md and the page carries no id and stays.
- No routine reads or writes `index.html` content that depends on these links (`tools/build-fragment.py` copies the page as is). `starter-story.html` and `learning-matrix.html` are untouched.
- The ids remain in git history; rewriting it is Ty's call (CLAUDE.md).
- Promise: `git grep -E 'trig_[A-Za-z0-9]{6,}'` prints nothing at head, and the next Pages run is green and serves the page with the same nine rows.
