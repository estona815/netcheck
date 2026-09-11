# NetCheck backend validation

Run on September 11, 2026, in the project directory:

```text
python3 -m unittest discover -s tests -v
Ran 15 tests in 0.011s
OK
exit_code: 0
```

Measured scope: original standard-library parser, graph, draft and report core only. Tests cover partial versus complete evidence wording; an actual multi-hop cross-net witness; confirmed observation and removal without source mutation; stale/double confirmation and stale export; grounded pin inspection; malformed/duplicate/unknown/self-loop input; byte/row/label limits; strict boolean; escaped hostile labels; non-colliding tuple pin IDs; exact source hashing; repeated deterministic output; empty observations; Unicode/quoted commas.

The fifteenth test exhaustively enumerates all 64 undirected graphs on four pins with two expected nets. It checks cross-net and disconnected-group results against an independent transitive-closure computation, and verifies every reported witness edge against its actual wire ID. These are test cases, not user-study observations or physical circuit measurements.

No filesystem or network behavior exists in the core. No model, Strands integration, browser UI, public deployment or physical hardware test was run by the core producer. The separate integration owner is responsible for actual model behavior and host confirmation boundaries. The supplied confirmation hash binds a reviewed state; it is not proof of a human action without that host boundary.

Core source and tests are handed off with stable API. Existing input files were not overwritten or removed; new project-local source/docs were created. Runtime caches are ignored by .gitignore and were preserved, not cleaned.
