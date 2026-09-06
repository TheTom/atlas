# Original Qwen3.8 FP8 H100 correctness result

Native original-checkpoint FP8 support is now implemented and observed on H100, in three commits on this PR:

- `b2029a45`: original block-FP8 loader/operator support, preserving 128×128 scale grids, matrix tails, tensor offsets and separate projection origins.
- `de5485c4`: developer-only `serve-local` entrypoint for the pinned HF snapshot; product catalog guards remain unchanged.
- `dfc45a185fc36ee84a8351eef21ae1dfc56d527a`: retain native block-FP8 MTP matrices instead of requiring floating-point storage. The first failed boot is preserved; this fixes it without skipping MTP tensors or re-quantizing them.

**Actual checkpoint:** `Qwen/Qwen3.8-27B-FP8`, revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, read directly from the existing Hugging Face snapshot. Staging proof SHA256 `6074590b1089e054afc8a4c2a23ca5e8a4184e4ff2c8ccb7898fa722cf812479`. This is separate from the earlier Q4_K_M report.

**Precision:** original E4M3FN weight bytes and original BF16 block multipliers (expanded exactly to F32), with F32 activations/accumulation. This is a CUDA-core W8A32 correctness baseline, not an optimized Hopper W8A8 Tensor Core claim. Iron remains pinned to composite `a4c897ba2e89db49df82b9d2f2691642d8f8b697` (299 + 315).

**Observed gates:**

| Check | Result |
|---|---|
| Independent GPU numerical oracles | 3/3 PASS, exact FP32 bits: partial/non-square blocks, unequal K-block scales, projection views, and dense128-lane reduction |
| Native checkpoint boot | PASS, health ready; 32,279MiB GPU memory used after loading |
| Determinism / tool schema / think-off | PASS / PASS / PASS |
| Arithmetic391 / Tokyo | PASS / PASS |
| Reverse refrigerator | FAIL: `rotaregifer`, expected `rotaregirfer`; finish_reason=stop |
| Plain / tool SSE structure | PASS / PASS, complete usage/terminal events; typed tool args `{"city":"Reykjavik","days":3}` |

The full frozen coherency JSON remains failed (exit1). The user's explicit exception for this reversal question is recorded separately; all other checks passed. No frozen ladder or certified performance result is claimed here. Tool-call SSE is emitted at completion in this observed response, so first-tool-delta time must not be described as the first internal generation token.

Exact tested source `dfc45a185fc36ee84a8351eef21ae1dfc56d527a`; saved CUDA binary SHA256 `da3e60000d55a2aaca67c04b09cd0400553444e45653d911ae828f06103cf606`. Build used `cargo build --locked --release -p wh-butter-cli --bin butter --no-default-features --features cuda,developer-cli` with the pinned nightly. CPU evidence: loader91pass/12ignored; final models407pass/3ignored plus doctest1; ops51pass; CLI routing red2fail→green2pass and product-command exclusion1pass. GPU test executable's build source is recorded separately; its operator/core/backend/test/lock paths were verified unchanged by the MTP-only fix.

Serve args were `serve-local --model <pinned snapshot absolute path> --max-context 8192 --parallel 1 --host 127.0.0.1 --port 8890`. The HTTP model identifier is that exact path. Original failed boot, fresh successful full gate, numerical output, raw requests/SSE, source/binary/weight identities and teardown are retained locally under `/Users/tom/Documents/New project/atlas-campaign-evidence/rental-live/butter-iron-followon/h100/`, especially `results/butter-block-fp8-http-20260906T000408Z/` and `butter-block-fp8-success-sha256.json`. GPU was stopped and occupancy successfully empty at **2026-09-06T00:05:12.790699Z**.
