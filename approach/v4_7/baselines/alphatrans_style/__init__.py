from __future__ import annotations

"""AlphaTrans-style ablation baseline for Java-to-C++ translation.

The baseline follows the AlphaTrans pipeline structure but drops the LLM-based
header scheme / method mapping stages of the full SITP pipeline:

  1. Program decomposition (reuse graph build: method fragments + call graph).
  2. Skeleton construction: deterministic rule-based Java-to-C++ type/signature
     translation (no LLM planning), producing one .h per class with method
     declarations and empty bodies.
  3. Compositional translation: methods translated in reverse call order
     (callees before callers), each prompted with its Java source, the
     translated callee signatures, and the class skeleton.
  4. Validation: clang++ compile check on generated .cpp files; on failure the
     offending method is reprompted with the compiler error (budget-limited),
     then the file is regenerated and recompiled.

This isolates the value of the LLM-driven header scheme, method mapping, and
agent repair of the full pipeline: the baseline keeps the same graph, same
LLM backend, and same compile gate, so results are directly comparable.
"""
