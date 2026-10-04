# Validation: Persistent Text and Quarto Wiki

Use synthetic fixtures only. Commands below describe acceptance stages; actual results and current holds
are recorded in tasks.md.

1. Run focused package tests with CPUWeight 20, nice 10 and cores 4-7:
   `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 npm run test:wiki-consistency`.
   Inspect `.qmd` discovery/special pages, metadata defaults/overrides, exact
   locator evidence and negative cases, log rename and cache-only bibliography.
2. Run similarly scoped raw-import, profile/mapping and integration tests. Read
   back generated synthetic pages and catalog; inspect local qmd collection masks.
   Delete synthetic cache and confirm raw/text/Wiki history survives.
3. After develop grants a vault writer window, take a fresh local preservation
   snapshot, apply the scoped migration and read back every body, metadata, log
   prefix, raw digest and foreign index. Report aggregate counts only.
4. Synchronize current develop into the feature without guessed conflict
   resolution. Freeze the combined commit/tree and request develop's full verify slot with
   attempt paths. Check `pgrep -af '[t]urbo run'` immediately before starting.
   Run the granted `npm run verify` under the same low-priority scope and retain
   start/exit plus the same Turbo summary. Inspect actual outputs.
5. Obtain fresh other-provider review on the combined frozen commit/tree, renew
   affected verification/review after material fixes, then submit exact evidence
   to develop for integration; do not finish
   or final-approve the change here.

New batch conversion, student-bearing raw decisions, site audience and
publication stay held with main. Missing locators/review evidence remain explicit
unverifiable results rather than broadening judgment input.

`prepare` is the exact-citation gate: reason-bearing diagnostic JSON with any
unverifiable unit exits 1. The separate offline `check` validates structure,
metadata, links and rules; its exit 0 cannot prove sentence evidence. Existing
uncited bodies and unknown text provenance are preserved, not silently checked.
