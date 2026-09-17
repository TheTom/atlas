// SPDX-License-Identifier: AGPL-3.0-only
//
// W4A16 prefill-GEMM microbenchmark driver for the R9700 (gfx1201, SCALE 1.7.1).
//
// Loads the device object built from `scripts/scale-probe/w4a16_gemm_bench.cu`
// with the CUDA DRIVER API: `cuModuleLoadData` on the `--cuda-device-only -c`
// relocatable, exactly as `spark-runtime` loads Atlas's own modules, resolves
// each requested kernel by SYMBOL NAME, verifies it against a CPU reference on
// a small tile, and reports TFLOP/s at the real prefill shapes.
//
// It exists because the R9700 prefill audit
// (`amd-rig-handoff/audit/PREFILL-ANALYSIS.md`) had to DERIVE the ~1.07 and
// ~4.11 TFLOP/s figures from end-to-end TTFT: nothing in the tree could
// measure one GEMM. A serve is a 40-second experiment with a dozen confounds;
// this is a two-second one with none.
//
// ═══════════════════════════════════════════════════════════════════════════
// BUILD AND RUN: on the board, from the repository root
// ═══════════════════════════════════════════════════════════════════════════
//   SCALE_HOME=${SCALE_HOME:-/opt/scale}
//
//   "$SCALE_HOME/targets/gfx1201/bin/nvcc" \
//       --cuda-device-only -c -O3 \
//       --fmad=false -DTQ_PLUS_SIGNS -ffp-contract=off \
//       scripts/scale-probe/w4a16_gemm_bench.cu -o /tmp/w4a16_gemm_bench.o
//
//   g++ -O2 -std=c++17 scripts/scale-probe/w4a16_bench.cpp -o /tmp/w4a16_bench \
//       -I"$SCALE_HOME/include" -L"$SCALE_HOME/lib" \
//       -Wl,-rpath,"$SCALE_HOME/lib" -lcuda -lnuma
//
//   /tmp/w4a16_bench --object /tmp/w4a16_gemm_bench.o
//
// `-lnuma` is there because SCALE's libcuda pulls it in; drop it if the link
// succeeds without. If `cuda.h` is not under `$SCALE_HOME/include`, point `-I`
// at whichever directory the SCALE install puts it in, this file needs no
// other header.
//
// ═══════════════════════════════════════════════════════════════════════════
// OPTIONS
// ═══════════════════════════════════════════════════════════════════════════
//   --object PATH     the device object to load (required in practice)
//   --device N        CUDA device ordinal (default 0)
//   --iters N         timed iterations per shape (default 20)
//   --warmup N        untimed iterations per shape (default 3)
//   --shape MxNxK     replace the default shape list; repeatable
//   --kernel SPEC     replace the default kernel list; repeatable. SPEC is
//                     `name[:layout:tileN:tileM:block:nargs]`, e.g.
//                       --kernel w4a16_gemm_rdna4_v2:packed:128:128:256:8
//                     layout is `packed` ([N,K/2], the HuggingFace order) or
//                     `transposed` ([K/2,N], the twin order). With only a name,
//                     a built-in entry is used if the name is known, otherwise
//                     the defaults `packed:128:128:256:8` apply, which is the
//                     convention `w4a16_gemm_rdna4` uses, so a NEW RDNA 4 arm
//                     can be A/B-ed as just `--kernel my_new_name`.
//   --no-verify       skip the correctness tile (do not; it is ~10 ms)
//   --verify-only     run the correctness tile and stop
//
// A kernel the object does not define is REPORTED AND SKIPPED, not fatal: the
// point of the harness is to compare what is there.
//
// ═══════════════════════════════════════════════════════════════════════════
// THE NVFP4 LAYOUT THIS FILE IMPLEMENTS
// ═══════════════════════════════════════════════════════════════════════════
// Byte-for-byte the layout `kernels/gb10/common/quantize_bf16_to_nvfp4.cu`
// writes and every `w4a16_*` kernel reads (HuggingFace compressed-tensors):
//
//   B_packed [N, K/2]   uint8, low nibble = W[n, 2j], high nibble = W[n, 2j+1]
//   B_scale  [N, K/16]  FP8 E4M3, one per group of 16 CONSECUTIVE K
//   scale2   f32 scalar, per tensor
//   dequant  w = E2M1[nibble] * e4m3(scale) * scale2
//
// and the quantizer is the same two-phase rule:
//   scale2       = global_absmax / (6 * 448)
//   group scale  = e4m3_encode(group_absmax / scale2 / 6)
//   nibble       = e2m1_nearest(w / (e4m3_decode(group_scale) * scale2))
//
// The transposed arms (`w4a16_gemm_t`, `w4a16_gemm_t_m128`) read the SAME
// bytes in `[K/2, N]` and `[K/16, N]` order, so this file builds those by
// plain 2-D transposition of the two arrays above rather than by re-quantizing
//, which is also what `weight_loader/qwen35_dense/transposed_twins.rs` does,
// so the twin arm is measured on the bytes it really gets.
//
// E4M3 decode is the STANDARD 1-4-3 bias-7 format, by bit math. It is NOT
// `(float)__nv_fp8_e4m3`: on SCALE that built-in decodes a non-standard narrow
// format (1.0 -> 1.5, 0.5 -> 1.0, 3.5 -> 2.75), which is why every kernel in
// this family routes through `scl_fp8` under `__SCALE__`.

#include <cuda.h>

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

// ── driver-API plumbing ────────────────────────────────────────────────────

static void cu_check(CUresult r, const char* what, const char* file, int line) {
    if (r == CUDA_SUCCESS) {
        return;
    }
    const char* name = nullptr;
    const char* msg = nullptr;
    cuGetErrorName(r, &name);
    cuGetErrorString(r, &msg);
    std::fprintf(stderr, "%s:%d: %s failed: %s (%d) %s\n", file, line, what,
                 name ? name : "?", static_cast<int>(r), msg ? msg : "");
    std::exit(1);
}
#define CU(expr) cu_check((expr), #expr, __FILE__, __LINE__)

// ── BF16 / FP8-E4M3 / E2M1, mirroring the device sources exactly ───────────

static inline float bf16_to_f32(uint16_t h) {
    uint32_t bits = static_cast<uint32_t>(h) << 16;
    float f;
    std::memcpy(&f, &bits, sizeof(f));
    return f;
}

// Round-to-nearest-even, which is what `__float2bfloat16` does.
static inline uint16_t f32_to_bf16(float f) {
    uint32_t bits;
    std::memcpy(&bits, &f, sizeof(bits));
    if ((bits & 0x7FFFFFFFu) > 0x7F800000u) {
        return 0x7FC0u;  // NaN
    }
    uint32_t lsb = (bits >> 16) & 1u;
    bits += 0x7FFFu + lsb;
    return static_cast<uint16_t>(bits >> 16);
}

// `float_to_fp8_e4m3` from quantize_bf16_to_nvfp4.cu, restated.
static inline uint8_t f32_to_e4m3(float v) {
    uint32_t bits;
    std::memcpy(&bits, &v, sizeof(bits));
    uint32_t sign = (bits >> 31) & 1u;
    if ((bits & 0x7FFFFFFFu) == 0u) {
        return static_cast<uint8_t>(sign << 7);
    }
    float absv = std::fabs(v);
    if (absv > 448.0f) {
        absv = 448.0f;
    }
    std::memcpy(&bits, &absv, sizeof(bits));
    int f32_exp = static_cast<int>((bits >> 23) & 0xFFu) - 127;
    uint32_t f32_man = bits & 0x7FFFFFu;
    if (f32_exp < -9) {
        return static_cast<uint8_t>(sign << 7);
    }
    if (f32_exp < -6) {
        int man = static_cast<int>(absv * 512.0f + 0.5f);
        if (man > 7) {
            man = 7;
        }
        if (man < 0) {
            man = 0;
        }
        return static_cast<uint8_t>((sign << 7) | static_cast<uint32_t>(man));
    }
    int e = f32_exp + 7;
    uint32_t m;
    if (e < 1) {
        e = 1;
    }
    if (e > 15) {
        e = 15;
        m = 6;
    } else {
        m = (f32_man + (1u << 19)) >> 20;
        if (m > 7u) {
            m = 0u;
            e++;
            if (e > 15) {
                e = 15;
                m = 6u;
            }
        }
    }
    return static_cast<uint8_t>((sign << 7) | (static_cast<uint32_t>(e) << 3) | m);
}

// Standard E4M3 decode: `scl_fp8` / `w4a16_rdna4_fp8`, restated.
static inline float e4m3_to_f32(uint8_t b) {
    uint32_t s = (b >> 7) & 1u;
    uint32_t e = (b >> 3) & 0xFu;
    uint32_t m = b & 0x7u;
    float v;
    if (e == 0u) {
        v = static_cast<float>(m) * 0.001953125f;
    } else if (e == 15u && m == 7u) {
        v = 0.0f;
    } else {
        uint32_t bits = ((e + 120u) << 23) | (m << 20);
        std::memcpy(&v, &bits, sizeof(v));
    }
    return s ? -v : v;
}

static const float kE2M1[16] = {0.0f, 0.5f, 1.0f, 1.5f, 2.0f, 3.0f, 4.0f, 6.0f,
                                -0.0f, -0.5f, -1.0f, -1.5f, -2.0f, -3.0f, -4.0f, -6.0f};

// `quantize_e2m1` from quantize_bf16_to_nvfp4.cu, restated.
static inline uint32_t f32_to_e2m1(float v) {
    float a = std::fabs(v);
    uint32_t sign = (v < 0.0f) ? 8u : 0u;
    uint32_t idx;
    if (a <= 0.25f) {
        idx = 0u;
    } else if (a <= 0.75f) {
        idx = 1u;
    } else if (a <= 1.25f) {
        idx = 2u;
    } else if (a <= 1.75f) {
        idx = 3u;
    } else if (a <= 2.5f) {
        idx = 4u;
    } else if (a <= 3.5f) {
        idx = 5u;
    } else if (a <= 5.0f) {
        idx = 6u;
    } else {
        idx = 7u;
    }
    return sign | idx;
}

// ── deterministic inputs ───────────────────────────────────────────────────
//
// xorshift64*, seeded per tensor, so two runs on two machines see the SAME
// bytes. A benchmark whose inputs move cannot be compared across iterations of
// this work, and "random" data whose seed is the clock is the usual way that
// happens.
struct Rng {
    uint64_t s;
    explicit Rng(uint64_t seed) : s(seed ? seed : 0x9E3779B97F4A7C15ull) {}
    uint64_t next_u64() {
        s ^= s >> 12;
        s ^= s << 25;
        s ^= s >> 27;
        return s * 0x2545F4914F6CDD1Dull;
    }
    // Roughly N(0, 1), by the sum of 4 uniforms, plenty for a GEMM whose only
    // numerical requirement is that no group is degenerate.
    float next_normal() {
        float acc = 0.0f;
        for (int i = 0; i < 4; i++) {
            acc += static_cast<float>(next_u64() >> 40) / 16777216.0f - 0.5f;
        }
        return acc * 1.7320508f;
    }
};

struct Nvfp4Weight {
    std::vector<uint8_t> packed;       // [N, K/2]
    std::vector<uint8_t> scale;        // [N, K/16]
    std::vector<uint8_t> packed_t;     // [K/2, N]
    std::vector<uint8_t> scale_t;      // [K/16, N]
    std::vector<float> dequant;        // [N, K] as the kernels see it, for the reference
    float scale2 = 0.0f;
};

// Quantize a dense [N, K] BF16 weight, mirroring
// `nvfp4_global_absmax` + `quantize_bf16_to_nvfp4`.
static Nvfp4Weight quantize_nvfp4(const std::vector<uint16_t>& w_bf16, uint32_t N, uint32_t K,
                                  bool want_dequant) {
    Nvfp4Weight out;
    const size_t groups = static_cast<size_t>(K) / 16u;

    float global_max = 0.0f;
    for (uint16_t h : w_bf16) {
        float v = std::fabs(bf16_to_f32(h));
        if (v > global_max) {
            global_max = v;
        }
    }
    out.scale2 = global_max / (6.0f * 448.0f);
    const float inv_scale2 = (out.scale2 > 0.0f) ? (1.0f / out.scale2) : 0.0f;

    out.packed.assign(static_cast<size_t>(N) * (K / 2u), 0u);
    out.scale.assign(static_cast<size_t>(N) * groups, 0u);
    if (want_dequant) {
        out.dequant.assign(static_cast<size_t>(N) * K, 0.0f);
    }

    for (uint32_t n = 0; n < N; n++) {
        const uint16_t* row = w_bf16.data() + static_cast<size_t>(n) * K;
        uint8_t* prow = out.packed.data() + static_cast<size_t>(n) * (K / 2u);
        uint8_t* srow = out.scale.data() + static_cast<size_t>(n) * groups;
        for (size_t g = 0; g < groups; g++) {
            const size_t base = g * 16u;
            float gmax = 0.0f;
            for (int i = 0; i < 16; i++) {
                float v = std::fabs(bf16_to_f32(row[base + i]));
                if (v > gmax) {
                    gmax = v;
                }
            }
            const float want = (gmax > 0.0f) ? (gmax * inv_scale2 / 6.0f) : 0.0f;
            const uint8_t sb = f32_to_e4m3(want);
            srow[g] = sb;
            const float eff = e4m3_to_f32(sb) * out.scale2;
            const float inv_eff = (eff > 0.0f) ? (1.0f / eff) : 0.0f;
            for (int i = 0; i < 16; i += 2) {
                const uint32_t n0 = f32_to_e2m1(bf16_to_f32(row[base + i]) * inv_eff);
                const uint32_t n1 = f32_to_e2m1(bf16_to_f32(row[base + i + 1]) * inv_eff);
                prow[g * 8 + i / 2] = static_cast<uint8_t>((n1 << 4) | (n0 & 0xFu));
                if (want_dequant) {
                    // The PLAIN kernel's association: mag * e4m3 * scale2.
                    // The RDNA 4 arm folds the last two, which is a
                    // reassociation and therefore a source of a few ulps -
                    // the reason the verdict below is a tolerance and not an
                    // equality.
                    const float s8 = e4m3_to_f32(sb);
                    out.dequant[static_cast<size_t>(n) * K + base + i] =
                        kE2M1[n0] * s8 * out.scale2;
                    out.dequant[static_cast<size_t>(n) * K + base + i + 1] =
                        kE2M1[n1] * s8 * out.scale2;
                }
            }
        }
    }

    // The twin layouts are the SAME bytes, transposed.
    out.packed_t.assign(out.packed.size(), 0u);
    for (uint32_t n = 0; n < N; n++) {
        for (uint32_t kp = 0; kp < K / 2u; kp++) {
            out.packed_t[static_cast<size_t>(kp) * N + n] =
                out.packed[static_cast<size_t>(n) * (K / 2u) + kp];
        }
    }
    out.scale_t.assign(out.scale.size(), 0u);
    for (uint32_t n = 0; n < N; n++) {
        for (size_t g = 0; g < groups; g++) {
            out.scale_t[g * N + n] = out.scale[static_cast<size_t>(n) * groups + g];
        }
    }
    return out;
}

// ── the kernels under test ─────────────────────────────────────────────────

enum class Layout { Packed, Transposed };

struct KernelSpec {
    std::string name;
    Layout layout = Layout::Packed;
    uint32_t tile_n = 128;
    uint32_t tile_m = 128;
    uint32_t block = 256;
    int nargs = 8;  // 9 adds the transposed-B row stride `ldb`
    const char* note = "";
};

// The built-in table. Every entry is read straight off its kernel's source and
// its Rust launcher in `crates/spark-model/src/layers/ops/gemm_dense.rs`.
static std::vector<KernelSpec> builtin_specs() {
    return {
        {"w4a16_gemm", Layout::Packed, 64, 64, 128, 8,
         "plain arm; the 27B measured ~4.11 TFLOP/s end-to-end on this one"},
        {"w4a16_gemm_rdna4", Layout::Packed, 128, 128, 256, 8,
         "RDNA 4 arm; 64 acc VGPRs, no cp.async, 40 KB LDS"},
        {"w4a16_gemm_t_m128", Layout::Transposed, 128, 128, 128, 8,
         "twin arm; __launch_bounds__(128,3) + 128 acc VGPRs + cp.async (S1/S2)"},
        {"w4a16_gemm_t", Layout::Transposed, 128, 64, 128, 9,
         "twin arm, 64-row M tile; the SSM out_proj arm today"},
    };
}

static bool parse_spec(const std::string& text, KernelSpec* out) {
    std::vector<std::string> parts;
    size_t start = 0;
    while (start <= text.size()) {
        size_t colon = text.find(':', start);
        if (colon == std::string::npos) {
            parts.push_back(text.substr(start));
            break;
        }
        parts.push_back(text.substr(start, colon - start));
        start = colon + 1;
    }
    if (parts.empty() || parts[0].empty()) {
        return false;
    }
    if (parts.size() == 1) {
        for (const KernelSpec& k : builtin_specs()) {
            if (k.name == parts[0]) {
                *out = k;
                return true;
            }
        }
        out->name = parts[0];
        out->note = "unknown name: assuming the w4a16_gemm_rdna4 convention";
        return true;
    }
    if (parts.size() != 6) {
        std::fprintf(stderr, "--kernel: expected `name` or `name:layout:tileN:tileM:block:nargs`, got `%s`\n",
                     text.c_str());
        return false;
    }
    out->name = parts[0];
    if (parts[1] == "packed") {
        out->layout = Layout::Packed;
    } else if (parts[1] == "transposed") {
        out->layout = Layout::Transposed;
    } else {
        std::fprintf(stderr, "--kernel: layout must be `packed` or `transposed`, got `%s`\n",
                     parts[1].c_str());
        return false;
    }
    out->tile_n = static_cast<uint32_t>(std::atoi(parts[2].c_str()));
    out->tile_m = static_cast<uint32_t>(std::atoi(parts[3].c_str()));
    out->block = static_cast<uint32_t>(std::atoi(parts[4].c_str()));
    out->nargs = std::atoi(parts[5].c_str());
    out->note = "from --kernel";
    if (out->tile_n == 0 || out->tile_m == 0 || out->block == 0 ||
        (out->nargs != 8 && out->nargs != 9)) {
        std::fprintf(stderr, "--kernel: tileN/tileM/block must be > 0 and nargs must be 8 or 9\n");
        return false;
    }
    return true;
}

struct Shape {
    uint32_t m, n, k;
};

struct DeviceShape {
    CUdeviceptr a = 0;
    CUdeviceptr bp = 0;   // [N, K/2]
    CUdeviceptr bs = 0;   // [N, K/16]
    CUdeviceptr bpt = 0;  // [K/2, N]
    CUdeviceptr bst = 0;  // [K/16, N]
    CUdeviceptr c = 0;
    float scale2 = 0.0f;
    size_t c_elems = 0;
};

static uint32_t div_ceil(uint32_t a, uint32_t b) { return (a + b - 1u) / b; }

static void launch(const KernelSpec& spec, CUfunction fn, const DeviceShape& dev, const Shape& s,
                   CUstream stream) {
    CUdeviceptr bp = (spec.layout == Layout::Packed) ? dev.bp : dev.bpt;
    CUdeviceptr bs = (spec.layout == Layout::Packed) ? dev.bs : dev.bst;
    // Local copies: cuLaunchKernel takes POINTERS to the arguments, and the
    // kernel's `ldb` is the transposed-B row stride, which is N whenever the
    // twin is built unpadded (it always is here).
    CUdeviceptr a = dev.a;
    CUdeviceptr c = dev.c;
    float scale2 = dev.scale2;
    uint32_t m = s.m, n = s.n, k = s.k, ldb = s.n;
    void* args[9] = {&a, &bp, &bs, &scale2, &c, &m, &n, &k, &ldb};
    CU(cuLaunchKernel(fn, div_ceil(s.n, spec.tile_n), div_ceil(s.m, spec.tile_m), 1, spec.block, 1,
                      1, 0, stream, args, nullptr));
    (void)spec.nargs;  // the 9th slot is simply ignored by an 8-param kernel
}

// ── main ───────────────────────────────────────────────────────────────────

static void usage() {
    std::printf(
        "usage: w4a16_bench --object OBJ [--device N] [--iters N] [--warmup N]\n"
        "                   [--shape MxNxK ...] [--kernel SPEC ...]\n"
        "                   [--no-verify] [--verify-only]\n");
}

int main(int argc, char** argv) {
    std::string object_path;
    int device = 0;
    int iters = 20;
    int warmup = 3;
    bool verify = true;
    bool verify_only = false;
    std::vector<Shape> shapes;
    std::vector<KernelSpec> specs;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        auto need = [&](const char* what) -> const char* {
            if (i + 1 >= argc) {
                std::fprintf(stderr, "%s needs a value\n", what);
                std::exit(2);
            }
            return argv[++i];
        };
        if (arg == "--object") {
            object_path = need("--object");
        } else if (arg == "--device") {
            device = std::atoi(need("--device"));
        } else if (arg == "--iters") {
            iters = std::atoi(need("--iters"));
        } else if (arg == "--warmup") {
            warmup = std::atoi(need("--warmup"));
        } else if (arg == "--no-verify") {
            verify = false;
        } else if (arg == "--verify-only") {
            verify_only = true;
        } else if (arg == "--shape") {
            Shape s{};
            if (std::sscanf(need("--shape"), "%ux%ux%u", &s.m, &s.n, &s.k) != 3) {
                std::fprintf(stderr, "--shape wants MxNxK\n");
                return 2;
            }
            shapes.push_back(s);
        } else if (arg == "--kernel") {
            KernelSpec spec;
            if (!parse_spec(need("--kernel"), &spec)) {
                return 2;
            }
            specs.push_back(spec);
        } else if (arg == "-h" || arg == "--help") {
            usage();
            return 0;
        } else {
            std::fprintf(stderr, "unknown argument `%s`\n", arg.c_str());
            usage();
            return 2;
        }
    }
    if (object_path.empty()) {
        std::fprintf(stderr, "--object is required\n");
        usage();
        return 2;
    }
    if (specs.empty()) {
        specs = builtin_specs();
    }
    if (shapes.empty()) {
        // The four the audit budgets. Qwen3.8-27B: hidden 5120, intermediate
        // 17408. Ornith-1.0-9B: hidden 4096, intermediate 12288. M = 3000 is
        // the 2973-token prefill rounded up.
        shapes = {{3000, 17408, 5120}, {3000, 5120, 17408}, {3000, 12288, 4096},
                  {3000, 4096, 12288}};
    }

    CU(cuInit(0));
    CUdevice dev;
    CU(cuDeviceGet(&dev, device));
    char dev_name[256] = {0};
    CU(cuDeviceGetName(dev_name, sizeof(dev_name) - 1, dev));
    CUcontext ctx;
    CU(cuCtxCreate(&ctx, 0, dev));

    std::vector<char> image;
    {
        FILE* f = std::fopen(object_path.c_str(), "rb");
        if (!f) {
            std::fprintf(stderr, "cannot open %s\n", object_path.c_str());
            return 1;
        }
        std::fseek(f, 0, SEEK_END);
        long len = std::ftell(f);
        std::fseek(f, 0, SEEK_SET);
        image.resize(static_cast<size_t>(len) + 1, 0);
        if (std::fread(image.data(), 1, static_cast<size_t>(len), f) != static_cast<size_t>(len)) {
            std::fprintf(stderr, "short read on %s\n", object_path.c_str());
            return 1;
        }
        std::fclose(f);
    }
    CUmodule mod;
    CU(cuModuleLoadData(&mod, image.data()));

    std::printf("device: %s (ordinal %d)\nobject: %s\n\n", dev_name, device, object_path.c_str());

    // Resolve up front, so a missing symbol is reported once rather than per
    // shape. `cuModuleGetFunction` on a SCALE object that does not define the
    // name returns an error rather than a handle that dies at launch, but
    // only because the name is genuinely absent from the ELF; a module that
    // compiled to NO kernels at all is the case `atlas-core/src/elf_symbols.rs`
    // exists for, and it cannot arise here (this object always carries the
    // qwen3.6-27b arms).
    struct Resolved {
        KernelSpec spec;
        CUfunction fn;
    };
    std::vector<Resolved> live;
    for (const KernelSpec& spec : specs) {
        CUfunction fn = nullptr;
        CUresult r = cuModuleGetFunction(&fn, mod, spec.name.c_str());
        if (r != CUDA_SUCCESS || fn == nullptr) {
            std::printf("  SKIP %-22s not defined by this object\n", spec.name.c_str());
            continue;
        }
        live.push_back({spec, fn});
    }
    if (live.empty()) {
        std::fprintf(stderr, "no requested kernel is present in %s\n", object_path.c_str());
        return 1;
    }
    std::printf("\n");

    CUstream stream;
    CU(cuStreamCreate(&stream, CU_STREAM_NON_BLOCKING));

    auto build_shape = [&](const Shape& s, bool want_dequant, Nvfp4Weight* qw_out,
                           std::vector<uint16_t>* a_out) -> DeviceShape {
        Rng rng_a(0xA11A5ull ^ (static_cast<uint64_t>(s.m) << 32) ^ s.k);
        Rng rng_b(0xB0B0Bull ^ (static_cast<uint64_t>(s.n) << 32) ^ s.k);
        std::vector<uint16_t> a(static_cast<size_t>(s.m) * s.k);
        for (uint16_t& x : a) {
            x = f32_to_bf16(rng_a.next_normal() * 0.05f);
        }
        std::vector<uint16_t> b(static_cast<size_t>(s.n) * s.k);
        for (uint16_t& x : b) {
            x = f32_to_bf16(rng_b.next_normal() * 0.02f);
        }
        Nvfp4Weight qw = quantize_nvfp4(b, s.n, s.k, want_dequant);

        DeviceShape d;
        d.scale2 = qw.scale2;
        d.c_elems = static_cast<size_t>(s.m) * s.n;
        CU(cuMemAlloc(&d.a, a.size() * 2));
        CU(cuMemcpyHtoD(d.a, a.data(), a.size() * 2));
        CU(cuMemAlloc(&d.bp, qw.packed.size()));
        CU(cuMemcpyHtoD(d.bp, qw.packed.data(), qw.packed.size()));
        CU(cuMemAlloc(&d.bs, qw.scale.size()));
        CU(cuMemcpyHtoD(d.bs, qw.scale.data(), qw.scale.size()));
        CU(cuMemAlloc(&d.bpt, qw.packed_t.size()));
        CU(cuMemcpyHtoD(d.bpt, qw.packed_t.data(), qw.packed_t.size()));
        CU(cuMemAlloc(&d.bst, qw.scale_t.size()));
        CU(cuMemcpyHtoD(d.bst, qw.scale_t.data(), qw.scale_t.size()));
        CU(cuMemAlloc(&d.c, d.c_elems * 2));
        CU(cuMemsetD8(d.c, 0, d.c_elems * 2));
        if (qw_out) {
            *qw_out = std::move(qw);
        }
        if (a_out) {
            *a_out = std::move(a);
        }
        return d;
    };

    auto free_shape = [](DeviceShape& d) {
        for (CUdeviceptr p : {d.a, d.bp, d.bs, d.bpt, d.bst, d.c}) {
            if (p) {
                cuMemFree(p);
            }
        }
        d = DeviceShape{};
    };

    int failures = 0;

    // ── correctness tile ───────────────────────────────────────────────────
    //
    // Small enough to reference on the CPU in milliseconds, and shaped so that
    // every tail the kernels predicate is exercised:
    //   M = 100  is a multiple of neither 128 (RDNA 4 / t_m128) nor 64 (plain)
    //   N = 208  is a multiple of 16 but not of 128 or 64
    //   K = 272  is 17 groups of 16, so the RDNA 4 arm's BK=32 loop meets a
    //            HALF-FULL last step and its K predicates have to hold
    // N stays a multiple of 16 because the twin arms' B loads are 16-byte
    // `cp.async` and row r sits at r*ldb, an unaligned N faults them with
    // CUDA_ERROR_MISALIGNED_ADDRESS (the campaign's long-standing 716), which
    // would be a property of the harness rather than of the kernel.
    if (verify) {
        const Shape vs{100, 208, 272};
        Nvfp4Weight qw;
        std::vector<uint16_t> a;
        DeviceShape d = build_shape(vs, true, &qw, &a);

        std::vector<double> ref(static_cast<size_t>(vs.m) * vs.n, 0.0);
        for (uint32_t i = 0; i < vs.m; i++) {
            for (uint32_t j = 0; j < vs.n; j++) {
                double acc = 0.0;
                for (uint32_t kk = 0; kk < vs.k; kk++) {
                    // Both kernels round the dequantized weight to BF16 before
                    // the MMA, so the reference must too, or the comparison
                    // measures the quantizer instead of the kernel.
                    float bw = bf16_to_f32(f32_to_bf16(qw.dequant[static_cast<size_t>(j) * vs.k + kk]));
                    acc += static_cast<double>(bf16_to_f32(a[static_cast<size_t>(i) * vs.k + kk])) *
                           static_cast<double>(bw);
                }
                ref[static_cast<size_t>(i) * vs.n + j] = acc;
            }
        }
        double ref_absmax = 0.0;
        for (double v : ref) {
            ref_absmax = std::fmax(ref_absmax, std::fabs(v));
        }

        std::printf("verify  M=%u N=%u K=%u   (reference |C|max = %.6f)\n", vs.m, vs.n, vs.k,
                    ref_absmax);
        std::vector<uint16_t> got(d.c_elems);
        for (const Resolved& r : live) {
            CU(cuMemsetD8(d.c, 0, d.c_elems * 2));
            launch(r.spec, r.fn, d, vs, stream);
            CU(cuStreamSynchronize(stream));
            CU(cuMemcpyDtoH(got.data(), d.c, d.c_elems * 2));
            double worst = 0.0;
            for (size_t i = 0; i < ref.size(); i++) {
                worst = std::fmax(worst, std::fabs(bf16_to_f32(got[i]) - ref[i]));
            }
            // BF16 outputs carry ~3 decimal digits, so the floor of what any
            // correct kernel can achieve is one output ulp: 2^-8 of |C|max.
            // 4x that admits the accumulation-order and dequant-association
            // differences between the arms and still fails a real bug by
            // orders of magnitude. NEVER loosen this to make an arm pass -
            // an arm that needs a looser bound is an arm with a bug.
            const double tol = ref_absmax * (4.0 / 256.0);
            const bool ok = worst <= tol;
            std::printf("  %-22s max|err| = %.6f   tol = %.6f   %s\n", r.spec.name.c_str(), worst,
                        tol, ok ? "PASS" : "FAIL");
            if (!ok) {
                failures++;
            }
        }
        std::printf("\n");
        free_shape(d);
    }
    if (verify_only) {
        cuStreamDestroy(stream);
        cuModuleUnload(mod);
        cuCtxDestroy(ctx);
        return failures == 0 ? 0 : 1;
    }

    // ── timing ─────────────────────────────────────────────────────────────
    CUevent ev0, ev1;
    CU(cuEventCreate(&ev0, CU_EVENT_DEFAULT));
    CU(cuEventCreate(&ev1, CU_EVENT_DEFAULT));

    for (const Shape& s : shapes) {
        DeviceShape d = build_shape(s, false, nullptr, nullptr);
        const double flops = 2.0 * static_cast<double>(s.m) * s.n * s.k;
        std::printf("M=%-6u N=%-6u K=%-6u   %.3f GFLOP per launch\n", s.m, s.n, s.k, flops / 1e9);
        for (const Resolved& r : live) {
            for (int i = 0; i < warmup; i++) {
                launch(r.spec, r.fn, d, s, stream);
            }
            CU(cuStreamSynchronize(stream));
            CU(cuEventRecord(ev0, stream));
            for (int i = 0; i < iters; i++) {
                launch(r.spec, r.fn, d, s, stream);
            }
            CU(cuEventRecord(ev1, stream));
            CU(cuStreamSynchronize(stream));
            float ms = 0.0f;
            CU(cuEventElapsedTime(&ms, ev0, ev1));
            const double per_launch_s = (static_cast<double>(ms) / 1000.0) / iters;
            std::printf("  %-22s %8.3f ms   %7.2f TFLOP/s   grid=(%u,%u) block=%u   %s\n",
                        r.spec.name.c_str(), per_launch_s * 1000.0, flops / per_launch_s / 1e12,
                        div_ceil(s.n, r.spec.tile_n), div_ceil(s.m, r.spec.tile_m), r.spec.block,
                        r.spec.note);
        }
        std::printf("\n");
        free_shape(d);
    }

    cuEventDestroy(ev0);
    cuEventDestroy(ev1);
    cuStreamDestroy(stream);
    cuModuleUnload(mod);
    cuCtxDestroy(ctx);
    return failures == 0 ? 0 : 1;
}
