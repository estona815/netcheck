# NetCheck integration validation — 2026-09-11

Status: local prototype with real Strands/Ollama execution; not published or submitted. Whole task remains 22 candidates with only A01 and A04 verified final submissions.

Final code: 17 unittest tests passed in 0.012s using Python 3.12, from the NetCheck project directory: `python -m unittest discover -s tests -v`. A root-directory invocation initially failed package discovery; rerunning from the documented project directory passed. Host regression tests simulate terminal input, create actual JSON/HTML reports, and verify original files remain unchanged. They are not evidence of a real participant approving a change.

Actual model: Qwen2.5:7b through Strands 1.55.1 and local Ollama 0.34.0. v003 normal, ambiguous and injection workflows called real tools and exited zero. v005 explicit W9 removal generated the real proposal f07adc1f9fb62bc22097b873d080d6ab8655458ea7f916a194d6d878c518fbe7, leaving source snapshot 0cd317703ac64d42780ca9aea7be76f19a6b3971551902a036c4306ce543d2c4 unchanged. No model execution confirmed a change or exported files. Proposal tools now include deterministic current-record analysis and use already host-validated inputs; completion requires a real analysis-bearing tool rather than redundant model call order.

Known model defects: previous trials invented an LED/AUX association, described a cross-net pin as correctly wired, and claimed staging after a rejected tool. Even v005 said the witness path was now open although its proposal was NOT applied. Natural-language accuracy therefore FAILS; no general reliability or prompt-injection immunity claim. Model prose is marked unverified and excluded from deterministic final record_review and exported HTML/JSON. Exit zero means tool-workflow completion only.

Retained failed trials: qwen3 token exhaustion with no tools; v001 normal token exhaustion; v002/v003 invalid staging; v004 valid proposal but incomplete old call-order requirement. The current design addresses brittle tool arguments and redundant order dependency, not language-model accuracy. Untrusted CSV fixture produced no staged change or export in the tested run, which is bounded evidence only.

Independent review found stale proposals aborting export after a prior confirmation. Fixed by explicit stale skip, with regression coverage for stale skip/export and decline-first/approve-second. No automatic restaging or approval.

Submission gates remain: participant AWS account, Builder ID and required experience facts, enrollment, public submission materials and final official receipt. This archive is a reviewed source/evidence snapshot, not a completed contest entry. Runtime model weights, virtual environment, credentials and unrelated participant data are excluded.
