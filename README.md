# TranCoGlue

> Replication package for *"TranCoGlue: A Hierarchical Framework for
> Module-Level Java-to-C++ Translation"* (under review).

TranCoGlue translates a **Java module** — a core class set plus its dependency
closure — into a compilable, linkable, and test-passing C++ project. Instead of
translating files or methods in isolation, TranCoGlue first builds class-hierarchy
and method-call graphs over the whole module, then translates along those graphs
so that every unit is generated conditioned on the units it depends on.

The pipeline runs in four stages:

1. **Dependency Analysis** — parse the module into class-level and method-level
   translation units, and build a class-hierarchy graph and a method call graph.
   
2. **Class Hierarchy Translation** — group class-level units into
   dependency-aware batches (batch size 5, leaf-first), translate them group by
   group into C++ headers, and iterate with compiler feedback.
3. **Method Call Graph Translation** — layer the call graph topologically
   and translate method bodies bottom-up, each
   with its class's header and its already-translated callees as context.
4. **Compilation-Feedback Repair** — merge headers and implementations into
   `.cpp` files, compile in topological order, and let an autonomous agent
   (`read_file` / `write_file` / `edit_file` / `create_file` / `compile`) repair
   the remaining failures under bounded budgets.

---

## ✨ Highlights

- 🧩 **Module-level, graph-guided** — headers and methods are translated along
  the class-hierarchy and call graphs, targeting the cross-file symbol
  inconsistency that dominates per-file / per-method translation.
- 🔁 **Compile-in-the-loop everywhere** — batched header iteration, per-file
  `clang++` checks, and an agentic repair stage.
- 🧠 **Backbone-agnostic** — the same pipeline runs under DeepSeek-V3.2, GPT-5.1 and Qwen3.5-Plus.
- 📦 **Benchmark included** — the 35-module benchmark (787 Java files, 5,802
  methods, 6 source repositories) ships in `source_projects/` with a manifest.

---

## 📁 Repository Layout

```
TranGoGlue/
├── approach/                     TranCoGlue implementation
│   ├── main.py                   CLI entry point (all experiments)
│   ├── v4_7/                     the four-stage pipeline
│   │   ├── steps/                stage drivers (graph → headers → methods → repair)
│   │   └── scripts/              evaluation helpers (metrics, functional tests)
│   ├── graph/                    persisted graph data model (JSON)
│   ├── parser_tool/              Gradle/JavaParser tool: .java → structured JSON
│   ├── utils/                    LLM client, config loading
│   └── llm_config.example.json   provider configuration template
├── source_projects/              the 35-module benchmark
│   ├── <module>/                 one directory per module (flat or core+deps)
│   ├── _cpp_stubs/               hand-written C++ stubs (JUC etc.)
│   ├── modules_manifest.csv      per-module inventory (files, methods, layout)
│   └── README.md                 benchmark documentation
└── README.md                     this file
```

A run produces:

```
output/v4_7/<project>/<ai>/runs/<run_id>/
├── graph/                        persisted project graph, headers, method nodes
├── result/                       generated C++ files and run statistics
│   ├── compile_report/           compilation evaluation
│   ├── llm_trace.jsonl           per-call LLM usage
│   ├── llm_usage.json            run-level usage summary
│   └── stage_token_summary.json  token usage by stage
└── review/                       agent repair working copy
```

---

## 🧰 Requirements

**Host environment.** Windows / Linux / macOS with:

- **Python** ≥ 3.10 (the paper's runs used a Conda env named `sitp`);
- **JDK 21** — the parser tool uses Gradle 8.14.3 and does not support newer JDKs;
- **clang++** on `PATH` (the paper used clang++ 20.1.8);
- **Gradle** (bootstrapped by `approach/parser_tool/`).

**API keys.** At least one LLM provider is required. Copy the template and fill
in `api_key` / `base_url` / `model_name` for the keys you plan to use
(`deepseek`, `gpt`, `qwen`):

```powershell
Copy-Item approach/llm_config.example.json approach/llm_config.json
$env:SITP_LLM_CONFIG_FILE = (Resolve-Path 'approach/llm_config.json').Path
```

> 💡 All providers are accessed through OpenAI-compatible chat endpoints; any
> OpenAI-compatible gateway (e.g. OpenRouter) can be substituted via `base_url`.

---

## 🚀 Quick Start

```powershell
# from the repository root
conda activate sitp                       # or your Python ≥ 3.10 env
$python = Join-Path $env:CONDA_PREFIX 'python.exe'
$env:JAVA_HOME = '<JDK_21_HOME>'          # parser requires JDK 21
$env:SITP_SOURCE_PROJECTS_DIR = (Resolve-Path 'source_projects').Path
$env:SITP_LLM_MAX_CONCURRENT_TASKS = '6'  # per-provider request concurrency
```

Run one module end-to-end in the paper's standard configuration:

```powershell
& $python approach/main.py --ai deepseek --project Cookie --mode full
```

All paper hyperparameters are **fixed per mode** in `approach/main.py`
(`PAPER_STANDARD_CONFIG`: temperature 0.2, header batch size 5, 5 header
iteration rounds, 10 repair attempts per failed file, 150 module-wide repair
tool calls, `base,additional` test suites) — the command line only selects the
backbone model, the project, and the experiment entry (`--mode`).

Outputs land in `output/v4_7/Cookie/deepseek/runs/<run_id>/`. Resume an
interrupted run with `--resume`, rerun only the agent repair stage on an
existing run with `--mode repair --run-id <id>`.

---

## 🧪 Reproducing the Evaluation

All commands run from the repository root. `$ai` ∈ `{deepseek, gpt, qwen}`
(DeepSeek-V3.2 / GPT-5.1 / Qwen3.5-Plus); `$project` ∈ the 35 module names in `source_projects`

### 🎯 Overall Effectiveness (RQ3) and Error Reduction (RQ4)

Run TranCoGlue in the standard configuration (`--mode full`) for every
(module, model) pair — 35 modules × 3 models. Loop over modules:

```powershell
foreach ($m in Get-Content module_list.txt) {
  & $python approach/main.py --ai $ai --project $m --mode full
}
```

The two agentic baselines (AlphaTrans-style and Oxidizer-style) are separate
modes with their own fixed configurations:

```powershell
# AlphaTrans-style (skeleton-driven agentic translation)
& $python approach/main.py --ai $ai --project $m --mode alphatrans-baseline

# Oxidizer-style (type-driven compile-first fragments)
& $python approach/main.py --ai $ai --project $m --mode oxidizer-baseline
```

### 🧩 Ablation Study (RQ5)

Nine-module cohort, DeepSeek-V3.2. Each ablation is its own `--mode` that
changes exactly one aspect of the standard configuration:

| Group | Change | Mode |
| --- | --- | --- |
| complete | none | `--mode full` |
| Header-OneShot | no grouping, no feedback rounds | `--mode ablation-header-oneshot` |
| w/o Grouping | one header per request, feedback kept | `--mode ablation-wo-grouping` |
| w/o Context | no translated-callee context in method prompts | `--mode ablation-wo-context` |
| w/o Repair | repair stage disabled | `--mode ablation-wo-repair` |

Example (w/o Context):

```powershell
& $python approach/main.py --ai deepseek --project Cookie --mode ablation-wo-context
```

### 📏 Header Batch-Size Sensitivity (RQ6)

Repeat the standard run (DeepSeek-V3.2, same 9-module cohort) with
`--mode rq6-batch-size --header-batch-size N` for `N` in
`{1, 2, 3, 4, 5, 6, 9}`. Batch size 5 is identical to `--mode full` and needs
no separate run.

### ⏱️ Cost and Time Overhead (RQ7)

Token usage is recorded per run in `result/llm_trace.jsonl`,
`result/llm_usage.json`, and `result/stage_token_summary.json`; wall time is the
run duration. Compare against the two agentic baselines (section RQ3) on the
35 modules with DeepSeek-V3.2.

---

## ⚙️ Configuration Reference

`approach/main.py --help` lists every option. The command line only exposes
the experiment entries and operational flags:

| Option | Meaning |
| --- | --- |
| `--ai` | Backbone model key (`deepseek` / `gpt` / `qwen`) |
| `--project` | Module name from `source_projects/modules_manifest.csv` |
| `--mode` | Experiment entry: `full`, `ablation-header-oneshot`, `ablation-wo-grouping`, `ablation-wo-context`, `ablation-wo-repair`, `rq6-batch-size`, `alphatrans-baseline`, `oxidizer-baseline`, `repair` |
| `--header-batch-size` | Batch size for `--mode rq6-batch-size` only (required there) |
| `--run-id` / `--resume` / `--force-rebuild` | Run identity and resume control |
| `--test` | Offline mock mode for the LLM generator |

---

## 📦 Output and Metrics

Each run is evaluated on the paper's metrics from its `result/` directory:

- $CS_h$ / $CS_s$ / $CS_t$ — compile-only pass rates of generated headers,
  `.cpp` files, and both (micro-aggregated);
- $LS$ — module-level link success;
- $TS$ — pass rate of the planned functional tests (unbuilt / crashed /
  timed-out count as failures);
- $Err(\#)$ — deduplicated root compiler errors (Undefined Symbols / Duplicated
  Definitions / Header File Error / Other);
- CoreCov — core-method coverage by the Java test suites.

Evaluation helpers live in `approach/v4_7/scripts/` (per-run compilation
evaluation, functional-test evaluation). Repaired files stay under `review/`
unless `--apply-repair` copies them back into `result/`.

---

## 🙏 Acknowledgements

The benchmark modules are drawn from
[failsafe-lib/failsafe](https://github.com/failsafe-lib/failsafe),
[alibaba/jvm-sandbox](https://github.com/alibaba/jvm-sandbox),
[alibaba/easyexcel](https://github.com/alibaba/easyexcel),
[TooTallNate/Java-WebSocket](https://github.com/TooTallNate/Java-WebSocket),
Apache HttpClient, and [dromara/hutool](https://github.com/dromara/hutool),
[java-callgraph2](https://github.com/Adrninistrator/java-callgraph2)
We are grateful to their authors and maintainers.
