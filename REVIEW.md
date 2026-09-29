# REVIEW.md

What the reviewer agent (`agents/reviewer.md` in claude-config) checks on every PR to this repo. The three passes run in order, each in full. The last section holds this repo's own rules.

This file is never served: it is not in `.pages-allow`.

## Severity
- **Critical:** it will break something live or publish something it must not. A secret or token, personal data by value in a public repo, a newly served path that shouldn't be, a broken deploy, data loss, a gate bypass.
- **High:** wrong behaviour that will show up. A bug on a path that runs, a broken reference, a diff that does something other than what the PR says, a house rule broken in a way Ty would have to undo.
- **Medium:** it's wrong but contained. An edge case that isn't hit yet, a doc that disagrees with the code, a missing test for a changed behaviour.
- **Low:** clarity, naming, a stale comment.

When unsure between two levels, pick the higher one and say why.

## Pass 1: Bugs
- [ ] Logic: off-by-one, inverted condition, wrong variable, an unreachable branch, loop bounds.
- [ ] Edge cases: empty input, a missing file, a first run, a name with spaces or accents, a timezone (Hanoi is UTC+7; cron is UTC).
- [ ] References resolve: every path, heading anchor, script flag, workflow job name and file named in the diff exists in `files/` or in the base.
- [ ] Shell: quoting, `set -e` interactions, `$?` after a pipe, BSD vs GNU flags (the Mac runs BSD tools).
- [ ] Syntax: YAML, JSON, Python (3.9 on the Mac: no `match`, no `X | Y` types), HTML.
- [ ] The diff does what the PR description says, and nothing it doesn't say.

## Pass 2: Security
- [ ] Secrets by pattern: `ghp_`, `github_pat_`, `sk-`, `sk-ant-`, `AKIA`, `xox[bp]-`, private-key headers, `eyJ…` JWTs (a Supabase **service_role** JWT is always Critical), passwords in URLs, `?token=`/`?key=` in a link.
- [ ] Personal data **by value** in a public repo: a name with money, a phone number, an email address, an account number, an ID number. Referring to where the value lives is fine; the value itself isn't.
- [ ] Anything newly published: a path added to `.pages-allow`, or any new file in a repo still on legacy Pages.
- [ ] Workflow permissions widened (`permissions:`, `pull_request_target`, `secrets: inherit`), or a new third-party action not pinned to a sha.
- [ ] Test fixtures build fake secrets at run time; a token-shaped string typed into a file is a finding even if it's fake.

## Pass 3: House rules
- [ ] **Never by value:** a sensitive value is referenced, not quoted, in any file of a public repo, including `work/` docs.
- [ ] **Artifact mirror contract:** no Cowork preview URL and no artifact id in anything public or anything Ty is shown. (A registry row that records an id on the private Drive mount is the exception.)
- [ ] **Entity separation:** OMNI and ECOPM data, names and numbers never cross into each other's repo or page.
- [ ] **One change per `work/` folder:** the PR names its `work/<yymmdd>-<slug>/`; `intent.md` says accepted; `spec.md` says approved; the diff matches the spec's promise, with nothing extra.
- [ ] **`gate/` untouched** while it is frozen (until 2026-10-05).
- [ ] **One PR per merge command:** nothing in the diff merges or batches PRs (`gh pr merge` in a loop, the merge API).
- [ ] **Verify before you assert:** every number in a doc or page has a source named beside it or in its section.

## Repo-specific rules
Rules specific to pipeline-wiring. **Every standing ruling in the README applies as well, except its description of how Pages serves the repo (see below); a PR that breaks one is at least High, and Critical where a line below says so.** The lines below are the ones most often at risk.

- **Each page has one writer.** The weekly check writes `data/status.json` and `data/.last-check` only, never a page; `learning-matrix.html` is rewritten only by the Learning Matrix routine on the 2nd; the prose in `index.html` is edited by hand (README), and no routine writes `starter-story.html`. A change that gives a page a second writer is High.
- **Publishing has changed since the README was written.** Once Pages runs from GitHub Actions, only the paths in `.pages-allow` are served; the README's "a push is the publish" predates the allowlist.
- **`build/` is generated.** A hand-edited `build/` file in a diff is High (README, "Layout").
- **The mirror has silent failure modes** (README, "Publishing" and "Layout"): publishing `index.html` itself nests and renders blank; the two iframe files must exist beside the page; and `data/status.json` must be published beside it, or the live cells break. A publish step that misses any of these is High.
- **The builders are not interchangeable.** This repo's `tools/build-fragment.py` strips document wrappers; the Omni-TMDV and Ecopm-Sitecheck builders cut at `<title>` (README, "Publishing"). Copying one repo's builder into another is High.
- **The Learning Matrix lives here and nowhere else.** A change that recreates a standalone Starter Story or Learning Matrix is High. A dead artifact id means "retired", not "missing" (README, "The Learning Matrix lives here and nowhere else").
- **The page describes every pipeline, so it carries status only.** Heartbeats, stamps, schedules and preview states, never a pipeline's own figures. A business number from any dashboard on this page is High; OMNI or ECOPM data by value is **Critical**.
- **One address, one preview.** `https://ttrng3.github.io/pipeline-wiring/` is the only link. Ty ruled on 2026-09-29 that the page's preview links and the preview ids in `data/status.json` go; their removal is its own change (the weekly routine reads those ids, so they move into its prompt). Until that ships, the existing ones are known; a PR that **adds** a Cowork preview URL or artifact id anywhere in the repo is **Critical** (the repo is public).
- **Don't widen what is published.** A new path in `.pages-allow`, or a new kind of data in `data/`, is High and needs Ty. (Carried from Omni-TMDV's REVIEW.md; not stated in this repo's own files.)
