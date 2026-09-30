# Spec

Status: approved by Ty 30/09 ("Approve the 4 specs but skip Teams", in chat).

- `index.html`: every `claude.ai/artifact/` link goes (50 occurrences, 25 artifacts: 9 in section 1, 9 in section 3, 16 × 2 in the "Sixteen" table). Section 1's preview cells keep their pill as plain text (`in sync` / `behind` / `dead`, from `data/status.json`); section 3's third column says `exists`. Two sentences that described the links now say previews are opened from claude.ai → Artifacts and their links are not published here.
- `tools/collect_status.py`: the preview id column leaves `PIPELINES`; rows carry `preview: {state}` only. `--preview key=state` is unchanged.
- `data/status.json`: the nine `preview.id` values go; nothing else changes.
- Weekly routine prompt (private): gains a table of the nine preview ids by pipeline key, and step 2 reads ids from that table instead of `data/status.json`. This works both before and after the merge, so the prompt is updated first and the Sunday run does not depend on the ship order. Built from a same-turn `get`, byte-checked after.
- `CLAUDE.md`: its note that the ids are "due to move" now says where they live.

Promise:
1. `grep -rnE 'claude\.ai/artifact/[A-Za-z0-9]|[A-Za-z0-9]{22}' --exclude-dir=.git .` finds no preview or artifact id (trigger ids, prefixed `trig_`, are out of scope).
2. The collector runs clean and `data/status.json` has no `id` key; the page's script renders the nine pills from it.
3. The next routine run records 9/9 previews checked.
