# Evaluation and development checkpoint

Run `python evals/run_rounds.py` to repeat the local unittest suite three times and record actual logs in results.json. Repetition checks stability, not new coverage or independent samples.

The suite runs real pytest against a temporary failing project and checks the resulting JUnit XML. Other cases cover summary semantics, namespaces, multiple errors, traceback formats, source boundaries, missing files, line bounds, malformed XML, DTD rejection, input size, log attribution and output preservation.

Unmeasured: independent Agent root-cause reasoning, report/check-out drift resolution, actual fix quality, flaky detection, resource exhaustion, all JUnit dialects and concurrent hostile filesystem changes. No root-cause accuracy or time-saved metric is claimed.

Development steps: scope and official report reference → same-domain discovery → deterministic extractor → integration and boundary tests → repeated recorded runs → bilingual docs/CI → independent repository upload and readback. Repository creation remains a separate publication prerequisite if the connector lacks it.
