# Intent: put the Trade Journal wiki and its Mac collector on the wiring page

**Status:** accepted 2026-10-08 (Ty, "do the four items now", after "Pipeline Wiring: add the wiki pipeline row" was listed)
**Source:** chat, 2026-10-08

**Problem.** Trade-Journal #14–#17 (merged 07–08/10) added a wiki step to the Trade Journal routine and a Mac launchd job that collects the bots' day files. The wiring page shows neither, and section 5 ("Mac dependency") misses a new Mac-only job.

**Outcome.** Section 5 names the collector as a third Mac-only job, with its schedule and why it is Mac-bound; section 7 gets a dated "Changed 08/10" entry for the wiki, with the PRs and merge commits.

**Who and what is affected.** `index.html` (prose only); the Cowork preview after its next refresh.

**Constraints.** Status only, no figures from the journal; no preview id, trigger id or personal data; the Trade Journal schedule is unchanged, so `tools/collect_status.py`'s cron table is untouched.

**Open questions.** none known
