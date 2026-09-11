# NetCheck

Original local connection-record comparison tool, created for the proposed Agents for Humans entry on September 11, 2026. It combines deterministic graph analysis with a local Strands CLI. Actual Qwen2.5:7b runs invoked loading, comparison, pin inspection and proposal tools. Measured model errors and their limits are documented below and in evidence/. The source is publicly available; no physical circuit test or final contest submission is claimed.

It compares an expected pin-to-net table with a user-recorded wire table. It returns cross-net witness paths and disconnected expected groups. With partial observations, a disconnected group is explicitly unverified: an omitted record is not proof that a physical wire is missing. Connectivity means wire connectivity only; components do not create implicit electrical paths between their pins. The program does not simulate current, assess component characteristics, certify safety or control hardware.

Python 3.10+ standard library only. From this directory:

```sh
python3 -m unittest discover -s tests -v
```

CSV inputs are supplied as strings. Expected header: `component,pin,net`. Observed header: `wire_id,from_component,from_pin,to_component,to_pin`. Each pin appears exactly once in the expected map. Each wire connects two existing distinct pin IDs. CSV columns must appear in that exact order. Identifiers remain strings; component and pin form a tuple. Inputs allow quoted commas and Unicode, and reject duplicate wire IDs/endpoints, malformed columns, unknown pins and oversized input.

```python
from netcheck import load_connection_tables, compare_connectivity, render_report

state = load_connection_tables(
    'component,pin,net\nJ1,1,SIGNAL\nR1,1,SIGNAL\n',
    'wire_id,from_component,from_pin,to_component,to_pin\nw1,J1,1,R1,1\n',
    observations_complete=False,
)
analysis = compare_connectivity(state)
# Only after the host obtains explicit review/export confirmation:
report = render_report(state, confirmed_state_hash=state.state_hash)
# report contains JSON and escaped standalone HTML text, not filesystem paths.
```

`inspect_pin` provides neighbors and expected net members. `stage_observation` proposes an addition/removal without modifying the immutable snapshot. `confirm_observation` creates a new snapshot only when the reviewed proposal hash and source state agree. Replaying a stale proposal or exporting a stale state fails. Original input hashes remain with the result; confirmed draft revisions receive separate hashes. Removing a record is a draft correction, not a physical repair or source-file deletion.

The CLI exposes confirmation separately through `--review` on an interactive terminal. **Never register `confirm_observation` as a model tool.** A hash is a state-binding mechanism, not proof of human identity. This core has no authentication or authorization service. The model may propose observations; only the host can apply them after exact-hash review.

All functions are pure with respect to external systems: no filesystem path arguments, shell, network, downloads, credentials or hardware access. The host must choose a new report file through explicit export and avoid overwriting user input. CSV cell text is treated as data; HTML output escapes it. Reports are HTML/JSON, not spreadsheet CSV, and contain no model-generated executable markup.

Limits: at most 300 expected pins, 600 wire records, 256000 UTF-8 bytes per table, and 80 characters per label. This small prototype requires explicit net names, has no CAD import, visual board sensing or node alias inference, and is not evidence that a real circuit is safe or works. `consistent_with_expected_map` refers only to the supplied graph; retain the completeness flag and scope statement when presenting it.

The CLI uses a real Strands Python Agent with local Qwen2.5:7b on Ollama. It exposes bounded tools and writes genuine model/tool events to stdout. The host validates selected tables before inference. Model failures or replies without an actual analysis-bearing tool return a nonzero exit status; proposal tools also return the current record comparison. Participant AWS Account/Builder ID and event registration remain unresolved outside this package.

Actual model trials exposed incorrect prose, including an unsupported LED-to-net association and a claim that a rejected proposal was staged. Model text is therefore explicitly an **unverified draft**, never the final report. The separate `record_review` event contains only deterministic graph results and actual proposal objects. Exit zero establishes completion of the tool workflow, not correctness of the model's explanation. Exported HTML/JSON contains no generated prose.

Install the pinned Python dependency from `requirements.txt`, install Ollama, pull `qwen2.5:7b`, and start Ollama with `OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NO_CLOUD=1 ollama serve`. Then run `python -m netcheck.agent_cli --fixture`. The model download is approximately 4.7GB; allow additional memory and storage for execution. See `AGENT_INTEGRATION_NOTES.md` for the separate review/export flow and `ARCHITECTURE.md` for component boundaries.

See ORIGIN.md for authorship and QA.md for measured validation. MIT licensed.

## Recorded demonstration

[Watch the captioned demonstration](https://www.youtube.com/watch?v=tM4hwq-c5pk). It reformats actual local tool output and is paced for reading; it is not a real-time screen recording. Inputs are synthetic, and the demonstration harness supplies confirmation hashes. The video does not represent participant approval or physical circuit testing.
