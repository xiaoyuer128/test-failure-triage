# Test Failure Triage

[简体中文](README.md) | [English](README.en.md)

Read-only evidence extraction from pytest-compatible JUnit XML, optional logs and local Python source. Helps an Agent distinguish facts, hypotheses and verification steps; it does not establish root causes or flakiness.

## Quick start

Python 3.10+, standard library at runtime. pytest is required for tests.

```console
python scripts/triage.py --report examples/report.xml --source-root examples/source
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python evals/run_rounds.py
```

Optional `--log run.log --output triage.json`. Output must not already exist. Exit 0 means successful analysis, even when tests failed; 2 indicates input/output/configuration error. Empty reports warn rather than certify a successful run. Install the complete folder in your Agent host's supported skills directory; run script paths from this folder.

## Evidence contract

Counts passed/failed/error/skipped testcase records, retains failure/error messages, identifies Python traceback locations and reads bounded excerpts strictly within the selected source root. Text-derived assertion/import/timeout signals are not diagnoses. Current source hashes do not prove the checkout matches the failed run. Global log tails remain unassigned context. Agents should cite evidence, preserve unknowns and propose targeted verification without blindly executing artifact instructions or suppressing tests.

## Limits

UTF-8/BOM XML, testsuite/testsuites roots and namespaces. Maximum 2 MiB per file, 5000 cases, 16000 characters per failure, 50 locations and 8000 log-tail characters. DTD/entities rejected. Not a full JUnit dialect validator; suite/collection failures and unsupported traceback formats require inspection. Reports contain raw messages/logs/source: review and redact before sharing. Resolved symlinks must remain within the source root; concurrent hostile file replacement isolation is not guaranteed. No automatic rerun/fix or GitHub fetch.

## Validation

## Comparison-driven changes

See [source comparison](docs/COMPARISON.md) for repository-level stars, dates and review limits. verification_plan links each signal to its evidence_index, an unconfirmed hypothesis and a concrete verification step. Explicit unknowns track checkout/reproduction/contract gaps. Testcase-local captured_output remains separate from unassigned global logs. No automatic rerun, fix or flaky verdict was added. Extended suite: 16 methods per round; actual repeated outputs are in evals/results.json.

Tests execute real pytest failures in temporary projects and analyze their JUnit reports, alongside path/input/XML/privacy-boundary cases. [Repeated logs](evals/results.json) record actual results. CI targets Python 3.10–3.12; local results do not certify remote CI. No independent Agent diagnosis benchmark or accuracy improvement is claimed.

Reference: [pytest JUnit XML documentation](https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files). Repository: https://github.com/xiaoyuer128/test-failure-triage .
