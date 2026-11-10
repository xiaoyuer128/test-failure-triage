# Same-domain comparison — 2026-11-10

This is source review, not executed comparative benchmarking. Star numbers are repository totals shown by GitHub pages at lookup time and may be cached, not per-Skill adoption.

| Source | Repository stars | Observed strengths | Scope tradeoffs |
|---|---|---|---|
| [addyosmani/debugging-and-error-recovery](https://github.com/addyosmani/agent-skills/blob/main/skills/debugging-and-error-recovery/SKILL.md) | approximately 114.7k (header rounds to 115k) | Reproduce, localize, reduce, fix, add regression protection; environment/state isolation guidance | Broad agent-driven debugging workflow; inspected entrypoint does not supply this project's bounded JUnit evidence report; generic commands need repository adaptation |
| [NatureMetrics/debugging-and-error-recovery](https://github.com/NatureMetrics/coding-agent-specification/blob/main/skills/debugging-and-error-recovery/SKILL.md) | 0 | Similar systematic workflow, explicit treatment of error output as untrusted data, old-code/new-code regression proof | Related workflow rather than independent performance evidence; broad stop-the-line/fix guidance exceeds a read-only triage task |

Two related implementations are not two independent algorithm benchmarks. We borrow workflow ideas, not source text or automatic permissions. Another candidate, payloadcms/payload triage-ci-flake, returned 404 at its searched path and is excluded from verified comparison. Apache magpie candidate could not be fetched and is likewise excluded.

## Changes adopted

- Evidence-linked verification plans: each text signal maps to a bounded hypothesis and a concrete next check; confidence stays unconfirmed.
- Testcase-local system-out/system-err: preserve association without assigning global logs to every failure.
- Explicit environment/checkout/reproduction unknowns; do not patch merely to silence assertions.
- Skill guidance: isolate/reduce and test one hypothesis at a time; require meaningful regression proof after an authorized fix.

## Kept out of scope

Automatic reruns, git bisect, source mutation, flaky verdicts and CI account integration require evidence/environment beyond the current report parser. No accuracy gain is claimed. Local tests validate report mechanics, not Agent root-cause reasoning.
