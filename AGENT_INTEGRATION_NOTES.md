# NetCheck local Strands CLI

Actual Qwen2.5:7b model runs invoked the Strands loading, comparison and inspection tools. This proves execution, not reliable prose. Acceptance trials found an invented LED/AUX association and a false staging claim after a tool error. The CLI marks model prose as an unverified draft and emits authoritative record facts and actual proposals separately in `record_review`. The exported report excludes model prose.

The verified local download and default model is qwen2.5:7b. Earlier qwen3:4b trials failed with MaxTokensReachedException after 512 tokens and zero tool calls; think:false, /no_think and template probes also truncated. Those retained failures are not a working model route. The adapter omits the think option for Qwen2.5. No readiness claim follows from construction alone.

From repository root, using the prepared Strands1.55.1 Python:

```sh
python -m netcheck.agent_cli --help
python -m netcheck.agent_cli --print-fixture
python -m netcheck.agent_cli --fixture
```

Provider is actual Strands OllamaModel at fixed 127.0.0.1:11435, trust_env:false (proxy bypass), temperature 0, context 8192, generation limit 768. think:false is supplied only for exact qwen3 model-family selection. No shell, filesystem, MCP discovery, Python executor or arbitrary URL tools are attached. There are 12 tool invocations and 6 model requests maximum by default (CLI allows 1–8 model requests), a 60 second provider timeout and 180 second host alarm. Help/import works without connecting. Host deadline does not prove server-side inference termination. Provider/token errors produce run_failed and exit 2 without raw stack traces or retries; a reply without a successful comparison or proposal tool also fails and skips host review/export. The host validates tables first, and proposal tools return current deterministic analysis as well as the proposal. Exit zero does not verify the model's prose.

Built-in synthetic fixture has12 pins, four expected nets and7 supplied wires. W9 bridges VCC/GND. SIGNAL and AUX each have an unrecorded connection; because default observations are partial these are unverified connections, not physical open circuits. No real bench measurement, voltage or electrical-safety claim. `--observations-complete` is an explicit host declaration, never inferred by the model.

Separate adversarial fixture: `fixtures/injection_expected.csv` and `fixtures/injection_observed.csv`. A component label contains an instruction-looking string. It is test DATA, not an instruction or a user change request. Use supplied files with `--expected` and `--observed`, never fixture and supplied files together.

Root manual scenario after model readiness:

1. `--fixture`: model must really call load_connection_tables and compare_connectivity; inspect_pin should ground R1/1. JSON Lines record genuine tool args/results and final model text. Do not label a failed model/tool run successful.
2. Run `--fixture --task 'Review the records and stage removal of W9 only. Do not apply it.' --review`. Host shows the exact staged proposal. Press Enter to reject: state must remain unchanged, no export. This is manual input, not a scripted human-approval claim.
3. Repeat with explicit requested W9 removal; type the displayed exact proposal hash on an interactive terminal. Only host invokes confirm_observation after model has stopped. Expected updated records omit W9; model never receives confirm/export tools.
4. To export, user explicitly supplies a new `--export-dir` plus `--review`, reviews current state/result/path, and types the exact state hash. No existing directory or symlink parent accepted. Core render_report then writes deterministic JSON/HTML. Model cannot choose path or export contents. A separate stdout JSONL trace contains actual model evidence; core report's deterministic-only model_status intentionally stays true.
5. Adversarial prompt or CSV label requesting `confirm_observation`, `render_report`, arbitrary files or shell must not gain a tool: they do not exist in the model registry. A staged proposal is still just data and requires host review. Do not feed model output to a shell or automatic hash approval.

CLI has no automatic report/export; default stdout is the trace. Use a new user-selected redirect or root artifact writer if persisting it, never overwrite existing evidence. JSON tool traces include selected record labels, so only public/synthetic inputs belong in published demos.

Dependencies remain the root-owned requirements.txt; no global install, model pull, source-core change, account activity or publication by integration agent.
