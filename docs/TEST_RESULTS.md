# Verification record

2026-10-20: Python 3.9.6, local macOS.

- `python3 -m unittest discover -s tests -v`: 16 tests passed.
- `python3 -m personas demo --out examples/demo`: succeeded; 240 reference pairs, 720 predictions.
- Browser visual inspection: generated HTML headline, provenance banner and concept chart rendered correctly.
- Fixed a Python 3.9 f-string quoting error discovered by the initial test run; rerun passed.
- Coverage includes known metric calculations, rank ties, missing/duplicate predictions, invalid ratings, mixed provenance, real-import schema fixture, no-overwrite protection, paid-call cap, missing API key, malformed LLM outputs and mocked HTTP response handling.
- No real dataset or paid live API was used. The real-import test uses a clearly fabricated fixture solely to exercise validation logic.
- GitHub CI configuration targets Python 3.9 and 3.12; its remote outcome is separate from this local verification record.
