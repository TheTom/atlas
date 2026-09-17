// SPDX-License-Identifier: AGPL-3.0-only

// Atlas W4A16 dequant+GEMM, RDNA 4 (gfx1201) prefill variant.
//
//   C[M,N] = A[M,K] (BF16) * dequant(B_fp4[N,K/2] (packed E2M1))
//
// SAME ARGUMENT LIST AND SAME B LAYOUT as the plain `w4a16_gemm`
// (`w4a16_gemm.cu`), so the Rust dispatch swaps one handle and one grid:
//   (A, B_packed[N,K/2], B_scale[N,K/16], scale2, C, M, N, K)
// It needs NO transposed twin, which on this board is also 12.74 GiB of VRAM
// the model does not have to hold (`docs/porting/r9700-residency.md`).
//
// ═══════════════════════════════════════════════════════════════════════════
// WHY THIS FILE EXISTS
// ═══════════════════════════════════════════════════════════════════════════
// The R9700 prefill audit (amd-rig-handoff/audit/PREFILL-ANALYSIS.md, §3.6)
// measures the projection GEMMs at ~1.07 TFLOP/s on the `w4a16_gemm_t_m128`
// twin arm and ~4.11 TFLOP/s on the plain arm. The twin arm wins by 7.3x on
// GB10 and LOSES by 3.85x here. The audit names three suspects, and this
// kernel is written so that each one is structurally absent rather than
// mitigated, and every design decision below names the suspect it answers.
//
// S1: REGISTER SPILL under `__launch_bounds__(128, 3)` with 128 accumulator
//      VGPRs (`acc0[16][4]` + `acc1[16][4]`).
//      ANSWER: 128x128 CTA tile spread over 256 threads = 8 wave32 waves, so
//      the accumulator is 128*128/256 = 64 FP32 VGPRs per thread, HALF the
//      twin's, and the same count as `w4a16_gemm_t`, which is one of the two
//      arms the 27B actually reached 4.11 TFLOP/s on. `__launch_bounds__(256)`
//      declares the BLOCK SIZE and nothing else: no min-blocks-per-SM, so the
//      compiler is never handed an occupancy demand it can only meet by
//      spilling. RDNA 4 has 1536 VGPRs per SIMD in wave32; at ~128 VGPRs per
//      wave this still admits 12 waves per SIMD, and the real ceiling here is
//      LDS (below), not registers.
//
// S2: EMULATED `cp.async` with a full `cp.async.wait_group 0` drain per K
//      step, which SCALE must lower to a global load + LDS write + a full
//      `s_waitcnt`, turning the two-stage double buffer into serial
//      load-then-compute.
//      ANSWER: NO `cp.async` ANYWHERE. The K loop is
//        issue plain vectorized global loads for tile s+1 into REGISTERS
//        -> run the MMAs for tile s out of LDS
//        -> write the registers into the other LDS buffer
//        -> one __syncthreads()
//      The global-load latency is covered by the 32 MMA instructions each wave
//      issues in between, which is a property of the SOURCE ORDER rather than
//      of any asynchronous-copy instruction the target has to emulate. One
//      barrier per K step, not two.
//
// S3: `mma.sync.m16n8k16` on a wave32 WMMA machine whose native shape is
//      16x16x16.
//      NOT ANSWERED HERE, deliberately. This kernel keeps `mma.sync`, because
//      `kernels/r9700/HARDWARE.toml` records BF16 `mma.sync m16n8k16` as the
//      ONE MMA shape that compiles on gfx1201 through SCALE, the fragment
//      layout is NVIDIA's and SCALE owns the mapping, and the audit bounds S3
//      at a 2x ceiling rather than the 28x inversion being chased. A native
//      `__builtin_amdgcn_wmma_f32_16x16x16_bf16_w32` port is the NEXT step and
//      it is a 1-2 week job with a fragment-layout numerics gate; it is not
//      this change. What this kernel DOES do about S3 is give it a clean floor
//      to be measured against: with spills and the serial pipeline gone,
//      whatever gap remains against the roofline is S3's.
//
// ═══════════════════════════════════════════════════════════════════════════
// BUDGET (all numbers per CTA unless stated)
// ═══════════════════════════════════════════════════════════════════════════
//   CTA tile      BM=128, BN=128, BK=32
//   threads       256 (8 waves of 32), warps laid out 4 (M) x 2 (N)
//   per warp      32 rows x 64 cols  =  2 m-frags x 8 n-frags of m16n8k16
//   accumulators  2*8*4 = 64 FP32 VGPRs/thread   (twin arm: 128)
//   operands      8 A regs + 16 B regs per k-half, ~10 staging regs
//   LDS           A 2*128*40*2 = 20480 B
//                 B 2*128*40*2 = 20480 B
//                 total 40960 B : under the 48 KB the brief asked for and
//                 well under RDNA 4's HARD 65536 B per-workgroup cap, so ~3
//                 workgroups fit a WGP's 128 KB and there are co-resident
//                 waves to cover what is left of the memory latency.
//   pad           stride 32+8 = 40 halves = 80 bytes. 80 % 16 == 0 keeps every
//                 16-byte LDS store aligned, and 80/4 = 20 dwords is coprime
//                 enough with 32 banks that the eight `group_id` rows an MMA
//                 fragment read touches land on eight DISTINCT banks
//                 (20*{0..7} mod 32 = 0,20,8,28,16,4,24,12), conflict-free on
//                 the hot path.
//
// K-ALIGNMENT INVARIANT: NVFP4 stores one FP8 scale per 16 K values, so
// `B_scale` is `[N, K/16]` and K is a multiple of 16 BY CONSTRUCTION. Every
// vector load below is sized so that this alone guarantees its alignment
// (8-byte `uint2` on B_packed, 16-byte `uint4` on A rows), and the K tail is
// handled per 16-element sub-block. M and N tails are predicated.
//
// ═══════════════════════════════════════════════════════════════════════════
// WHERE THIS FILE LIVES, AND WHY NOT IN kernels/gb10/common
// ═══════════════════════════════════════════════════════════════════════════
// It is a REAL FILE in `kernels/r9700/common/`, declared in that target's
// `HARDWARE.toml [kernels] overrides`, and NOT a gb10 source mirrored here by
// symlink like the other 180 entries of this directory.
//
// That is the shape `scripts/check_cross_hardware.py` leaves open: its rule S1
// refuses a NEW cross-hardware symlink outright, `kernels/gb10/HARDWARE.toml`
// records the same refusal stranding `gated_delta_rule_chunk_tc.cu` in the
// Hopper tree: and its option (c) is "separate kernel in the intended tree,
// pinned to base bytes, NO symlink". It is also the maintainer rule
// `check_kernel_shadows.py` quotes (tbraun96, 2026-09-11): a target-tuned
// kernel must be a real file under that target, declared.
//
// It is the right shape on the merits too. Nothing here is arch-neutral: the
// tile, the thread count, the LDS budget and the absence of `cp.async` are all
// answers to gfx1201 measurements, and on an NVIDIA part the arm it replaces
// wins by 7.3x. So gb10, hopper and b200 do not compile this file at all -
// their builds are byte-identical, and no boot audit anywhere gains a row.
//
// ═══════════════════════════════════════════════════════════════════════════
// GUARD
// ═══════════════════════════════════════════════════════════════════════════
// The body is still `#if defined(__SCALE__)`, belt and braces: it states that
// the source is SCALE-only rather than merely filed under an AMD target, and
// it makes the file inert if it is ever symlinked or copied somewhere that
// compiles with nvcc or hipcc, where the `mma.sync` bodies would not build.

#if defined(__SCALE__)

#include <cuda_bf16.h>

#define W4A16_RDNA4_BM 128
#define W4A16_RDNA4_BN 128
#define W4A16_RDNA4_BK 32
#define W4A16_RDNA4_PAD 8
#define W4A16_RDNA4_STRIDE (W4A16_RDNA4_BK + W4A16_RDNA4_PAD)  // 40 halves = 80 B
#define W4A16_RDNA4_GROUP 16
#define W4A16_RDNA4_THREADS 256

// Standard E4M3 (1-4-3, bias 7) decode by pure bit math.
//
// NOT `(float)__nv_fp8_e4m3`: on SCALE that built-in decodes a NON-STANDARD
// narrow format (verified 1.0 -> 1.5, 0.5 -> 1.0, 3.5 -> 2.75), which
// mismatches the standard E4M3 block scales `quantize_bf16_to_nvfp4` writes
// and corrupts every group. The plain `w4a16_gemm` in
// `qwen3.6-27b/nvfp4/w4a16_gemm.cu` routes through the same bit math under
// `__SCALE__` for exactly this reason; this is that function, renamed so the
// two can share a translation unit in the microbench.
__device__ __forceinline__ float w4a16_rdna4_fp8(unsigned char b) {
    unsigned int s = (b >> 7) & 1u;
    unsigned int e = (b >> 3) & 0xFu;
    unsigned int m = b & 0x7u;
    float v;
    if (e == 0u) {
        v = (float)m * 0.001953125f;  // subnormal: m * 2^-9
    } else if (e == 15u && m == 7u) {
        v = 0.0f;  // NaN -> 0, same as the encoder's reserved pattern
    } else {
        v = __uint_as_float(((e + 120u) << 23) | (m << 20));  // 2^(e-7) * (1 + m/8)
    }
    return s ? -v : v;
}

// E2M1 nibble -> float, branchless, bit-exact with `E2M1_LUT`.
//
// A TABLE rather than arithmetic is what every other W4A16 kernel here uses:
// `__constant__` on NVIDIA, or a 64-byte LDS copy in the `_t_m128` SCALE arm.
// Both are the wrong shape on RDNA 4, a divergent index into the scalar
// constant cache serialises, and an LDS copy spends the same LDS issue slots
// the MMA fragment reads need, 4096 times per CTA per K step. This is ~4 VALU
// ops with no memory traffic at all.
//
//   magnitude index (nib & 7) -> 0, 0.5, 1, 1.5, 2, 3, 4, 6
//   e = (nib >> 1) & 3, m = nib & 1
//   e == 0 -> {0.0, 0.5};  e > 0 -> 2^(e-1) * (1 + m/2)
//   float bits: exponent e+126, mantissa m << 22;  sign is bit 3 of the nibble
__device__ __forceinline__ float w4a16_rdna4_e2m1(unsigned int nib) {
    unsigned int e = (nib >> 1) & 3u;
    unsigned int m = nib & 1u;
    unsigned int bits = (e == 0u) ? (m ? 0x3F000000u : 0u)
                                  : (((e + 126u) << 23) | (m << 22));
    bits |= (nib & 8u) << 28;
    return __uint_as_float(bits);
}

// C = A * dequant(B). See the header for the tile/thread/LDS budget.
//
// ★ The dequant folds the two scales ONCE PER GROUP, `s = e4m3 * scale2`,
// then `mag * s`: instead of the plain kernel's `mag * e4m3 * scale2`. That
// is a REASSOCIATION, so this kernel is NOT bit-identical to `w4a16_gemm`; it
// is the same association the `_t_m128` SCALE arm already ships
// (`sv0 = scl_fp8(...) * scale2`), and `scripts/scale-probe/w4a16_bench.cpp`
// grades it against a CPU reference and against the plain kernel's own output
// rather than asserting equality.
extern "C" __global__ __launch_bounds__(W4A16_RDNA4_THREADS) void w4a16_gemm_rdna4(
    const __nv_bfloat16* __restrict__ A,
    const unsigned char* __restrict__ B_packed,  // [N, K/2]
    const unsigned char* __restrict__ B_scale,   // [N, K/GROUP_SIZE]
    const float scale2,
    __nv_bfloat16* __restrict__ C,
    unsigned int M,
    unsigned int N,
    unsigned int K
) {
    const unsigned int cta_m = blockIdx.y * W4A16_RDNA4_BM;
    const unsigned int cta_n = blockIdx.x * W4A16_RDNA4_BN;

    const unsigned int t = threadIdx.x;
    const unsigned int warp_id = t >> 5;        // 0..7
    const unsigned int lane_id = t & 31u;
    const unsigned int warp_m = warp_id >> 1;   // 0..3 -> 32 rows each
    const unsigned int warp_n = warp_id & 1u;   // 0..1 -> 64 cols each
    const unsigned int group_id = lane_id >> 2; // m16n8k16 fragment row / col
    const unsigned int quad = lane_id & 3u;     // m16n8k16 fragment k pair

    // One barrier per K step is enough because the two buffers alternate: the
    // MMAs of step s read `cur`, the stores of step s write `1 - cur`, and the
    // barrier at the end of step s separates step s's reads of `cur` from step
    // s+1's writes of `cur`.
    __shared__ __nv_bfloat16 sA[2][W4A16_RDNA4_BM][W4A16_RDNA4_STRIDE];
    __shared__ __nv_bfloat16 sB[2][W4A16_RDNA4_BN][W4A16_RDNA4_STRIDE];

    // 2 m-fragments x 8 n-fragments x 4 = 64 FP32 VGPRs. This is the S1 answer.
    float acc[2][8][4];
    #pragma unroll
    for (int mi = 0; mi < 2; mi++) {
        #pragma unroll
        for (int nj = 0; nj < 8; nj++) {
            acc[mi][nj][0] = 0.0f;
            acc[mi][nj][1] = 0.0f;
            acc[mi][nj][2] = 0.0f;
            acc[mi][nj][3] = 0.0f;
        }
    }

    const unsigned long long half_K = (unsigned long long)(K >> 1);
    const unsigned long long num_groups = (unsigned long long)(K / W4A16_RDNA4_GROUP);

    // ── A staging: 128 rows x 32 halves = 8192 B over 256 threads = 32 B each.
    // Two threads cover one row (16 halves = one 32-byte uint4 pair each), so
    // four consecutive lanes cover two consecutive rows and a wave touches 16
    // rows. `gc` is a multiple of 16 and K is a multiple of 16, so a row's
    // 16-half chunk is either wholly in range or wholly out.
    const unsigned int a_row = t >> 1;                 // 0..127
    const unsigned int a_col = (t & 1u) << 4;          // 0 or 16
    const unsigned int a_gr = cta_m + a_row;

    // ── B staging: 128 columns x 32 nibbles = 2048 B over 256 threads = one
    // 8-byte `uint2` each (16 nibbles), plus the one FP8 group scale that
    // covers exactly those 16 K values. `half_K` is a multiple of 8 because K
    // is a multiple of 16, so the `uint2` is 8-byte aligned for every column.
    const unsigned int b_col = t >> 1;                 // 0..127
    const unsigned int b_sub = (t & 1u) << 4;          // 0 or 16 (K offset)
    const unsigned int b_gn = cta_n + b_col;

    uint4 a_reg0, a_reg1;
    uint2 b_reg;
    float b_scl;

    // Issue the global loads for K tile `kb` into registers. NO cp.async: this
    // is the S2 answer. Plain `global_load_dwordx4` / `dwordx2`, whose latency
    // the MMA block below covers because the consumer (the LDS store) is the
    // NEXT statement after it.
    #define W4A16_RDNA4_LOAD(kb)                                                       \
        do {                                                                           \
            unsigned int gc = (kb) + a_col;                                            \
            if (a_gr < M && gc < K) {                                                  \
                const uint4* src = (const uint4*)(A + (unsigned long long)a_gr * K + gc); \
                a_reg0 = src[0];                                                       \
                a_reg1 = src[1];                                                       \
            } else {                                                                   \
                a_reg0 = make_uint4(0u, 0u, 0u, 0u);                                   \
                a_reg1 = make_uint4(0u, 0u, 0u, 0u);                                   \
            }                                                                          \
            unsigned int gk = (kb) + b_sub;                                            \
            if (b_gn < N && gk < K) {                                                  \
                b_reg = *(const uint2*)(B_packed + (unsigned long long)b_gn * half_K   \
                                        + (unsigned long long)(gk >> 1));              \
                unsigned char sb = B_scale[(unsigned long long)b_gn * num_groups       \
                                           + (unsigned long long)(gk / W4A16_RDNA4_GROUP)]; \
                b_scl = w4a16_rdna4_fp8(sb) * scale2;                                  \
            } else {                                                                   \
                b_reg = make_uint2(0u, 0u);                                            \
                b_scl = 0.0f;                                                          \
            }                                                                          \
        } while (0)

    // Retire the staged registers into LDS buffer `buf`, dequantizing B on the
    // way in so the MMA loop below is PURE BF16 and never touches a nibble.
    // Both stores are 16-byte aligned: the row stride is 80 bytes and the
    // in-row offsets are 0 or 32.
    #define W4A16_RDNA4_STORE(buf)                                                     \
        do {                                                                           \
            uint4* adst = (uint4*)&sA[(buf)][a_row][a_col];                            \
            adst[0] = a_reg0;                                                          \
            adst[1] = a_reg1;                                                          \
            unsigned int bw[8];                                                        \
            /* Bytes come out of the two staged VGPRs by shifting. Taking the   */     \
            /* ADDRESS of `b_reg` instead would force it to scratch, which is   */     \
            /* the very spill this kernel exists to avoid.                      */     \
            _Pragma("unroll")                                                          \
            for (int w = 0; w < 2; w++) {                                              \
                unsigned int word = w ? b_reg.y : b_reg.x;                             \
                _Pragma("unroll")                                                      \
                for (int i = 0; i < 4; i++) {                                          \
                    unsigned int byte = (word >> (8 * i)) & 0xFFu;                     \
                    float lo = w4a16_rdna4_e2m1(byte & 0xFu) * b_scl;                  \
                    float hi = w4a16_rdna4_e2m1(byte >> 4) * b_scl;                    \
                    bw[w * 4 + i] =                                                    \
                        ((unsigned int)__bfloat16_as_ushort(__float2bfloat16(hi)) << 16) \
                        | (unsigned int)__bfloat16_as_ushort(__float2bfloat16(lo));    \
                }                                                                      \
            }                                                                          \
            uint4* bdst = (uint4*)&sB[(buf)][b_col][b_sub];                            \
            bdst[0] = make_uint4(bw[0], bw[1], bw[2], bw[3]);                          \
            bdst[1] = make_uint4(bw[4], bw[5], bw[6], bw[7]);                          \
        } while (0)

    // 32 `mma.sync` per wave per K step: 2 k-halves x 2 m-fragments x 8
    // n-fragments. The A fragment is hoisted out of the n loop, so the
    // activation tile is read once and reused across all 8 N fragments, the
    // reuse the brief asked for, and the reason a 128-wide N tile is worth its
    // LDS.
    #define W4A16_RDNA4_MMA(buf)                                                       \
        do {                                                                           \
            const unsigned short* pA = (const unsigned short*)&sA[(buf)][0][0];        \
            const unsigned short* pB = (const unsigned short*)&sB[(buf)][0][0];        \
            _Pragma("unroll")                                                          \
            for (int kh = 0; kh < 2; kh++) {                                           \
                unsigned int c0 = (unsigned int)(kh * 16) + quad * 2u;                 \
                unsigned int c1 = c0 + 8u;                                             \
                _Pragma("unroll")                                                      \
                for (int mi = 0; mi < 2; mi++) {                                       \
                    unsigned int r0 = warp_m * 32u + (unsigned int)(mi * 16) + group_id; \
                    unsigned int r1 = r0 + 8u;                                         \
                    unsigned int a0 = *(const unsigned int*)&pA[r0 * W4A16_RDNA4_STRIDE + c0]; \
                    unsigned int a1 = *(const unsigned int*)&pA[r1 * W4A16_RDNA4_STRIDE + c0]; \
                    unsigned int a2 = *(const unsigned int*)&pA[r0 * W4A16_RDNA4_STRIDE + c1]; \
                    unsigned int a3 = *(const unsigned int*)&pA[r1 * W4A16_RDNA4_STRIDE + c1]; \
                    _Pragma("unroll")                                                  \
                    for (int nj = 0; nj < 8; nj++) {                                   \
                        unsigned int nc = warp_n * 64u + (unsigned int)(nj * 8) + group_id; \
                        unsigned int b0 = *(const unsigned int*)&pB[nc * W4A16_RDNA4_STRIDE + c0]; \
                        unsigned int b1 = *(const unsigned int*)&pB[nc * W4A16_RDNA4_STRIDE + c1]; \
                        float* d = acc[mi][nj];                                        \
                        asm volatile(                                                  \
                            "mma.sync.aligned.m16n8k16.row.col.f32.bf16.bf16.f32 "     \
                            "{%0,%1,%2,%3},{%4,%5,%6,%7},{%8,%9},{%10,%11,%12,%13};"   \
                            : "=f"(d[0]), "=f"(d[1]), "=f"(d[2]), "=f"(d[3])           \
                            : "r"(a0), "r"(a1), "r"(a2), "r"(a3), "r"(b0), "r"(b1),    \
                              "f"(d[0]), "f"(d[1]), "f"(d[2]), "f"(d[3]));             \
                    }                                                                  \
                }                                                                      \
            }                                                                          \
        } while (0)

    const unsigned int steps = (K + W4A16_RDNA4_BK - 1u) / W4A16_RDNA4_BK;

    W4A16_RDNA4_LOAD(0u);
    W4A16_RDNA4_STORE(0);
    __syncthreads();

    unsigned int cur = 0u;
    for (unsigned int s = 0; s < steps; s++) {
        const bool more = (s + 1u) < steps;
        // Source order is the pipeline: loads first so their latency is
        // outstanding across the MMA block, the LDS store (which is what
        // actually waits on them) last.
        if (more) {
            W4A16_RDNA4_LOAD((s + 1u) * W4A16_RDNA4_BK);
        }
        // `cur` indexes the LDS arrays at RUNTIME rather than selecting between
        // two unrolled copies of the block: a shared-memory subscript is an
        // address offset, and duplicating 32 unrolled `mma.sync` twice would
        // cost instruction cache for nothing.
        W4A16_RDNA4_MMA(cur);
        if (more) {
            W4A16_RDNA4_STORE(cur ^ 1);
            __syncthreads();
            cur ^= 1;
        }
    }

    #undef W4A16_RDNA4_LOAD
    #undef W4A16_RDNA4_STORE
    #undef W4A16_RDNA4_MMA

    // Epilogue. `m16n8k16` gives each lane rows {group_id, group_id+8} and
    // columns {quad*2, quad*2+1} of every 16x8 fragment.
    #pragma unroll
    for (int mi = 0; mi < 2; mi++) {
        unsigned int r0 = cta_m + warp_m * 32u + (unsigned int)(mi * 16) + group_id;
        unsigned int r1 = r0 + 8u;
        #pragma unroll
        for (int nj = 0; nj < 8; nj++) {
            unsigned int c0 = cta_n + warp_n * 64u + (unsigned int)(nj * 8) + quad * 2u;
            unsigned int c1 = c0 + 1u;
            if (r0 < M && c0 < N) C[(unsigned long long)r0 * N + c0] = __float2bfloat16(acc[mi][nj][0]);
            if (r0 < M && c1 < N) C[(unsigned long long)r0 * N + c1] = __float2bfloat16(acc[mi][nj][1]);
            if (r1 < M && c0 < N) C[(unsigned long long)r1 * N + c0] = __float2bfloat16(acc[mi][nj][2]);
            if (r1 < M && c1 < N) C[(unsigned long long)r1 * N + c1] = __float2bfloat16(acc[mi][nj][3]);
        }
    }
}

#endif  // __SCALE__
