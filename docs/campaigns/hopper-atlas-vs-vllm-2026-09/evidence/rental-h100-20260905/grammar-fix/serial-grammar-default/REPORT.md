# Restore the historical serial grammar-preparation default

Commit `22cdda741d9d527b2318878639726fc1135d1243`, based on `e68079c7d70035b17f52af3a33ca70a61c2863c5`. Only `crates/spark-server/src/grammar/engine.rs` changes.

The parent observed H100 cold-auto first-tool times of 5.279 and 6.567 seconds with four workers after warm factoring, and 5.744 seconds after borrowing tokenizer input. The earlier baseline observation was 4.824 seconds. These observations do not demonstrate the intended cold-latency improvement. Warm decode and typed-call correctness remain improved, so those changes stay in place.

The engine now requests one compiler worker, its historical default. The compiler still accepts bounded parallel worker counts for callers; its exact mask tests compare serial and four-worker output. The 512-mask cap, borrowed tokenizer inputs, value-rule factoring, grammar constraints, recipe flags and environment remain unchanged.

No new timing threshold or test mirroring the worker constant was added. Existing 826 compiler unit tests, including full serial/parallel mask equality and worker completion, passed on identical compiler source in the previous batch. Actual native auto/required full masks and rollback also matched across one/four workers. Local formatting, touched-file typos and diff checks passed for this one-file change.

A new changed-server build/test has **not** run in this subtask. After staging an owned Spark 1 checkout, the other CPU agent conveyed the parent's no-new-build restriction at 2.8–2.9 GB free. No Cargo/build was started; the staged checkout was removed, with 2.9 GB free afterward. The parent assigned final combined server tests to the rental-host CPU gate owner.

Stopping rule: parent performs one H100 build/retest with the restored default, then stops this cold-latency investigation regardless of the outcome. Remaining shared-Arc reference-count contention is a hypothesis for later work, not a change in this commit.
