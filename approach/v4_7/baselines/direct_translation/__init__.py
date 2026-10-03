from __future__ import annotations

"""Direct (translation-only) baseline with optional compile-error feedback.

Corresponds to the "Translation Only" and "Error Feedback" baselines of
RepoTransBench: each Java file is translated to a C++ header/implementation pair
with no program decomposition, no skeleton construction, and no dependency
ordering. With `max_feedback_rounds > 0`, files that fail the clang++ compile
checks are reprompted with the compiler error logs (budget-limited), then
regenerated and recompiled.

The compile report is written to the same layout as the full pipeline
(result/compile_report/{header,cpp}_compile_summary.json), so the compile pass
rates are directly comparable.
"""
