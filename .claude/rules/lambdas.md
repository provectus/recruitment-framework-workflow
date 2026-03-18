---
globs:
  - "app/lambdas/**"
---

- All 5 Lambda functions share `shared/` layer (bedrock.py, config.py, db.py, evaluation_lifecycle.py)
- Two-tier model config: "heavy" (Sonnet) for screening_eval, technical_eval, recommendation; "light" (Haiku) for cv_analysis, feedback_gen
- When updating entity status in lifecycle functions, reset ALL status-related fields (error_message, started_at, etc.) — not just the ones relevant to the new status. A retry after failure means old failure state must be cleared.
- Lambda runtime is Python 3.12 — when building layers with `pip install --platform`, always pin `--python-version 3.12` to avoid host version mismatch (e.g. macOS Python 3.14 downloading cp314 wheels that Lambda can't load)
