# TranCoGlue — Paper Reproduction Package

This repository is the reproduction package for the paper's module-level
Java-to-C++ LLM translation study. It contains the full approach (`approach/`)
and the 35-module benchmark (`source_projects/`).

## 1. What the paper does

The paper presents **TranCoGlue**, a hierarchical framework for module-level
Java-to-C++ translation, together with an empirical study of how LLMs behave on
this task.

**Empirical study (RQ1–RQ2).** 35 modules from six open-source Java repositories
(failsafe, jvm-sandbox, easyexcel, httpclient, hutool, Java-WebSocket; 787 Java
files, 5,802 methods) are translated with three backbone LLMs (DeepSeek-V3.2,
GPT-5.1, Qwen3.5-Plus) under three strategies: **PFT** (per-file translation),
**PMT** (per-method translation), and **PMBT** (PMT with bottom-up call-graph
ordering). The study finds that cross-file symbol consistency is the dominant
bottleneck (undefined symbols are the largest error class under every strategy),
and that translation order changes the error profile — the findings that motivate
TranCoGlue's design.

**The approach (four stages, `v4_7` pipeline).**

1. **Dependency analysis** — JavaParser-based parsing into class-level and
   method-level translation units; construction of a class-hierarchy graph and a
   method call graph. Hand-written C++ stubs (`source_projects/_cpp_stubs/`, JUC
   etc.) are injected here as already-translated, read-only nodes.
2. **Class hierarchy translation** — class-level units are grouped into
   dependency-aware translation groups (leaf-first, batch size 5) and translated
   group by group; each round is validated with `clang++ -fsyntax-only` and failed
   units are regrouped and retranslated with diagnostics, for up to 5 rounds.
3. **Method call graph translation** — the call graph is topologically layered
   (Tarjan SCC folding for recursion) and translated bottom-up; each method's
   prompt includes its class's C++ header and the already-translated callees.
4. **Compilation-feedback repair** — headers and implementations are merged into
   `.cpp` files and compiled in topological order; an autonomous agent
   (`read_file` / `write_file` / `edit_file` / `create_file` / `compile`) repairs
   failures with a budget of 10 repair attempts per failed file and 150 tool
   calls per module.

**Evaluation (RQ3–RQ7).** RQ3 compares TranCoGlue against five baselines (PFT,
PMT, PMBT, AlphaTrans-style, Oxidizer-style) on all 35 modules × 3 models; RQ4
measures compilation-error reduction; RQ5 ablates grouping, iteration, context,
and repair on a 9-module cohort with DeepSeek-V3.2; RQ6 sweeps the header batch
size {1,2,3,4,5,6,9}; RQ7 reports token and time cost.

**Metrics.** $CS_h$ / $CS_s$ / $CS_t$: compile-only pass rate of generated
headers / `.cpp` files / both (micro-aggregated); $LS$: module-level link success
rate; $TS$: pass rate of the 164 planned functional tests (unbuilt/crashed/
timed-out count as failures); $Err(\#)$: deduplicated root compiler errors after
cascade suppression; CoreCov: core-method coverage by the Java test suites.

## 2. Setup

See `approach/README.md` for full details. In short:

```powershell
conda activate sitp                       # provides Python + deps
$env:JAVA_HOME = '<JDK_21_HOME>'          # parser requires JDK 21
clang++ --version                         # must be on PATH
Copy-Item approach/llm_config.example.json approach/llm_config.json
# fill in api_key / base_url / model_name for keys: deepseek, gpt, qwen
$env:SITP_LLM_CONFIG_FILE = (Resolve-Path 'approach/llm_config.json').Path
$env:SITP_SOURCE_PROJECTS_DIR = (Resolve-Path 'source_projects').Path
$env:SITP_LLM_MAX_CONCURRENT_TASKS = '6'  # per-provider request concurrency
```

All commands below run from the repository root with
`$python = Join-Path $env:CONDA_PREFIX 'python.exe'` and take `--ai` in
`{deepseek, gpt, qwen}` (DeepSeek-V3.2 / GPT-5.1 / Qwen3.5-Plus) and `--project`
in the 35 module names. Runs are stored under
`output/v4_7/<project>/<ai>/runs/<run_id>/` and resumable via `--resume` or
`--run-id`.

## 3. Main approach (RQ3)

The paper's standard configuration — temperature 0.2, header batch size 5, 5
header iteration rounds, 10 repair attempts per failed file, 150 module-wide
repair tool calls, base+additional test suites:

```powershell
& $python approach/main.py --ai deepseek --project Cookie --mode full `
  --temperature 0.2 --header-batch-size 5 --header-max-rounds 5 `
  --header-translation-mode batched_iterative --method-translation-mode contextual `
  --allow-header-failures --compile-timeout 60 `
  --repair-after-compile --apply-repair --max-repair-attempts 10 `
  --max-tool-calls 150 
```

## 4. Baselines (RQ3/RQ4/RQ7)

AlphaTrans-style and Oxidizer-style baselines are built into `main.py`:

```powershell
# AlphaTrans-style baseline (skeleton-driven agentic translation)
& $python approach/main.py --ai deepseek --project Cookie --mode alphatrans-baseline `
  --temperature 0.2 --compile-timeout 60 --max-repair-attempts 10 `
  --fragment-max-tries 10 --feature-requery-budget 10

# Oxidizer-style baseline (type-driven compile-first fragments)
& $python approach/main.py --ai deepseek --project Cookie --mode oxidizer-baseline `
  --temperature 0.2 --compile-timeout 60 --max-repair-attempts 10 `
  --fragment-max-tries 10 --feature-requery-budget 10
```

(`--mode direct-translation` and `--mode react-baseline` are also available.)
The PFT / PMT / PMBT baselines were run with the legacy v3 / v4 / v4_1 pipelines,
which are not part of this package.

## 5. Ablation study (RQ5)

All ablations start from the standard configuration of section 3 (DeepSeek-V3.2,
9-module cohort) and change one aspect:

| Group | Change | Command-line difference |
| --- | --- | --- |
| complete | none | section 3 as-is |
| Header-OneShot | no grouping, no feedback rounds | `--header-translation-mode per_file_one_shot --header-max-rounds 1` |
| w/o Grouping | one header per request, feedback kept | `--header-batch-size 1` |
| w/o Context | no translated-callee context | `--method-translation-mode no_context` |
| w/o Repair | repair stage disabled | drop `--repair-after-compile --apply-repair` |

Example (w/o Context):

```powershell
& $python approach/main.py --ai deepseek --project Cookie --mode full `
  --temperature 0.2 --header-batch-size 5 --header-max-rounds 5 `
  --header-translation-mode batched_iterative --method-translation-mode no_context `
  --allow-header-failures --compile-timeout 60 `
  --repair-after-compile --apply-repair --max-repair-attempts 10 `
  --max-tool-calls 150
```

## 6. Header batch-size sensitivity (RQ6)

Repeat the standard run with `--header-batch-size` in `{1, 2, 3, 4, 5, 6, 9}`;
batch size 5 is identical to the section-3 configuration.

## 7. Notes

- After changing source layouts, delete `output/v4_7/<project>/split` or pass
  `--force-rebuild`; otherwise stale graphs are silently reused.
- `--max-tool-calls` defaults to an auto-scaled budget
  (`max(150, 10 per header)`).
- If a run is interrupted, resume it with the same `--run-id` and the `--mode`
  of the stage to continue (`header` / `mapping` / `method` / `compile` /
  `repair`).
