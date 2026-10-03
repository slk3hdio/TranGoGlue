# TranGoGlue

TranGoGlue is the paper's Java-to-C++ translation method. The entry point is `approach/main.py`, which runs the `v4_7` pipeline: project graph construction, header planning and translation, method mapping and translation, C++ file generation, compilation checks, and optional agent repair.

## 1. Prerequisites

Run the following commands from the repository root. Use Python from the `sitp` Conda environment directly for batch or concurrent runs; parallel `conda run` processes can interfere with one another through shared temporary files.

```powershell
conda activate sitp
$python = Join-Path $env:CONDA_PREFIX 'python.exe'
$ai = '<model_key>'
$project = '<project_name>'
```

Graph construction requires JDK 21. If another JDK is the system default, replace the placeholder with the local JDK 21 installation directory:

```powershell
$env:JAVA_HOME = '<JDK_21_HOME>'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
```

Make sure `clang++` is also available on `PATH`:

```powershell
java -version
clang++ --version
```

Copy the sample provider configuration and fill in the provider details. The local configuration file is excluded by `.gitignore`; do not commit real API keys.

```powershell
Copy-Item approach/llm_config.example.json approach/llm_config.json
$env:SITP_LLM_CONFIG_FILE = (Resolve-Path 'approach/llm_config.json').Path
```

The configuration is a JSON object indexed by command-line model keys. Each entry requires `api_key`, `base_url`, and `model_name`. Use configured keys with `--ai` and `--mapping-ai`. You can instead pass the complete JSON through `SITP_LLM_CONFIG_JSON`; it takes precedence when both environment variables are set.

## 2. Run the full approach

This command uses the current recommended experiment settings: header batches of five, up to five header iteration rounds, ten repair attempts per failed file, a project-wide limit of 150 repair tool calls, and the base and additional functional test suites.

```powershell
& $python approach/main.py `
  --ai $ai `
  --project $project `
  --mode full `
  --temperature 0.2 `
  --header-batch-size 5 `
  --header-max-rounds 5 `
  --header-translation-mode batched_iterative `
  --method-translation-mode contextual `
  --allow-header-failures `
  --compile-timeout 60 `
  --repair-after-compile `
  --apply-repair `
  --max-repair-attempts 10 `
  --max-tool-calls 150 `
  --repair-test-suites base,additional
```

Change `$ai` and `$project` to run a different model or module. By default, method mapping uses the configured `gpt` key with thinking enabled. Use `--mapping-ai` to select another model or `--no-mapping-thinking` to disable thinking.

## 3. Control request concurrency

Set the number of concurrent LLM requests with an environment variable. Up to six requests per API platform is the recommended setting:

```powershell
$env:SITP_LLM_MAX_CONCURRENT_TASKS = '6'
& $python approach/main.py --ai $ai --project $project --mode full --header-batch-size 5
```

If a large prompt repeatedly stalls at the last request in a batch, reduce concurrency to one for the resumed run:

```powershell
$env:SITP_LLM_MAX_CONCURRENT_TASKS = '1'
```

## 4. Select another source-project set

The default input directory is `source_projects/`. To use the flat dependency-closure set in `source_projects_min50/`, set:

```powershell
$env:SITP_SOURCE_PROJECTS_DIR = (Resolve-Path 'source_projects_min50').Path
& $python approach/main.py --ai $ai --project $project --mode full --header-batch-size 5
```

In `source_projects_min50/`, dependency classes reside directly in each module root rather than in a `deps/` subdirectory.

## 5. Resume a run

The `v4_7` pipeline stores each experiment under a run ID:

```text
output/v4_7/<project>/<ai>/runs/<run_id>/
```

Resume the latest run for the selected model and project:

```powershell
& $python approach/main.py --ai $ai --project $project --resume --mode full --header-batch-size 5
```

To resume a specific run, set its ID and select the stage to continue:

```powershell
$runId = '<run_id>'
& $python approach/main.py `
  --ai $ai `
  --project $project `
  --run-id $runId `
  --mode method `
  --skip-mapping `
  --repair-after-compile `
  --apply-repair `
  --max-repair-attempts 10 `
  --max-tool-calls 150 `
  --repair-test-suites base,additional
```

Common stage-specific commands:

```powershell
# Rerun method mapping.
& $python approach/main.py --ai $ai --project $project --run-id $runId --mode mapping

# Reuse the existing mapping and continue method translation, compilation, and repair.
& $python approach/main.py --ai $ai --project $project --run-id $runId --mode method --skip-mapping --repair-after-compile --apply-repair --max-repair-attempts 10 --max-tool-calls 150

# Rerun compilation checks only.
& $python approach/main.py --ai $ai --project $project --run-id $runId --mode compile

# Repair existing output only.
& $python approach/main.py --ai $ai --project $project --run-id $runId --mode repair --apply-repair --max-repair-attempts 10 --max-tool-calls 150 --repair-test-suites base,additional
```

`--force-rebuild` deletes the selected run's existing `graph/` and `result/` directories before rebuilding them. Use it only when those results can be discarded. `--clear-method-progress` clears method mapping and translation progress.

## 6. Run modes

| Mode | Purpose |
| --- | --- |
| `full` | Run the complete main pipeline; this is the default mode. |
| `header` | Run header translation only. |
| `mapping` | Run Java-to-C++ method mapping only. |
| `method` | Run method translation and file generation, with optional compilation and repair. |
| `compile` | Check compilation of existing generated output. |
| `repair` | Repair existing failed output. |
| `alphatrans-baseline` | Run the AlphaTrans-style baseline. |
| `react-baseline` | Run the ReAct-style baseline. |
| `direct-translation` | Run the direct-translation baseline. |
| `oxidizer-baseline` | Run the Oxidizer-style baseline. |

For all available options:

```powershell
& $python approach/main.py --help
```

## 7. Output layout

A standard run typically contains:

```text
runs/<run_id>/
├── graph/                         # Persisted project graph, headers, and method nodes
├── result/                        # Generated C++ files and run statistics
│   ├── compile_report/            # Compilation evaluation
│   ├── llm_trace.jsonl            # Per-call LLM usage
│   ├── llm_usage.json             # Run-level usage summary
│   └── stage_token_summary.json   # Token usage by stage
└── review/                        # Agent repair working copy
```

With `--apply-repair`, repaired `.h` and `.cpp` files are copied from `review/` back into `result/`. Otherwise, the repairs remain in `review/`.

## 8. Troubleshooting

### The pipeline reuses an old graph after source files change

The pipeline can reuse `output/v4_7/<project>/split`. After changing source files or the dependency layout, remove that module's old `split` directory or use `--force-rebuild`; otherwise the pipeline may continue with stale graph data.

### Header iteration does not converge

A batch size of three can split inheritance relationships across batches. Use `--header-batch-size 5`. To keep the current header output and continue to later stages, add `--allow-header-failures`.

### Repair uses too many tool calls

Set `--max-tool-calls` explicitly. The current experiments commonly use 150. This is a project-wide limit on repair tool calls; `--max-repair-attempts 10` limits compilation attempts for each failed file.

### Provider billing errors or a stalled request

Check the provider balance and network connection. Resume with the same `--run-id` after an interruption. If high-concurrency runs repeatedly stall on the last request, temporarily set `SITP_LLM_MAX_CONCURRENT_TASKS` to `1`.

### Gradle and JDK are incompatible

The parser uses Gradle 8.14.3 and requires JDK 21. If the logs show JDK 25, set `JAVA_HOME` to JDK 21 before rerunning.
