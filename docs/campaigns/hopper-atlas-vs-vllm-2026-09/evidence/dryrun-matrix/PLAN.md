# Step D2 execution plan

Code oracle: b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b. Policy oracle: PRD on docs branch 0b21f2a, sections 3, 4, 5, 6, 7, 8 and 16.

1. Observe refusal of nonexistent model key, invalid spec, and Nano speculation before accepting any good render.
2. Enumerate all named model/SKU pairs. Expand lat 1024/256 and agent 4096/512 at C=1 and C=16; exercise both engines and both spec/think switches. Mark disallowed or unfrozen switches as policy probes, never as frozen scored cells. Keep explicitly named topology alternatives separately because the CLI has no topology selector.
3. For each cell capture argv, exit, full stdout and stderr from run_cell.sh --dry-run. For every vLLM cell also capture vllm_control.sh --dry-run. Do not invoke Docker, spark, GPU tools or network clients.
4. Independently parse rendered commands and compare complete vLLM token arrays to JSON, including spec removals/additions; check Atlas calibration, draft count and frozen ladder flags. Demonstrate auditor failure on deliberately corrupted in-memory argv before auditing real output.
5. Record policy drift, unsupported recipes and conflicting PRD requirements as findings; do not edit recipes or scripts to invent a policy. Collect focused CPU-only reproductions for any script defect.

Stopping rule: every enumerated cell has both applicable exits/output and an oracle verdict, or an execution block and evidence is recorded. Stop after two hours even if policy remains ambiguous; dry rendering cannot resolve model support or performance.
