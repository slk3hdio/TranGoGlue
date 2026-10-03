from __future__ import annotations

"""ReAct-style file-level translation baseline for Java-to-C++ translation.

This baseline follows the ReAct (Reasoning + Acting) paradigm of
RepoTransAgent (RepoTransBench, IEEE TSE 2026): instead of the SITP
pipeline's staged decomposition (header scheme -> method mapping ->
method translation -> compile check -> agent repair), a single LLM agent
drives each Java file end-to-end:

  1. Read the Java class source.
  2. Create the target C++ files (.h declaration + .cpp implementation).
  3. Compile the .cpp with clang++ (the only validation signal).
  4. Observe the compiler errors and iteratively edit the files until
     the code compiles or the interaction budget is exhausted.

The agent has the same tool set as the SITP repair agent
(read_file / write_file / edit_file / create_file / compile_file), the
same LLM backend, and the same compile gate, so file-level compile pass
rates are directly comparable with the full pipeline. There is no
skeleton, no decomposition, no method mapping, and no staged repair:
it isolates the value of SITP's staged decomposition + header scheme.
"""
