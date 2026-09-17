// SPDX-License-Identifier: AGPL-3.0-only

// W4A16 prefill-GEMM A/B object for the R9700 (gfx1201, SCALE 1.7.1).
//
// This translation unit exists so that ONE loadable code object carries EVERY
// W4A16 prefill arm the board can run, and `scripts/scale-probe/w4a16_bench.cpp`
// can launch any of them by SYMBOL NAME with the same argument convention. It
// declares no kernels of its own: it aggregates the real sources, unmodified,
// so a number measured here is a number about the kernel Atlas actually ships.
//
//   from kernels/gb10/qwen3.6-27b/nvfp4/w4a16_gemm.cu (the source the r9700
//   tree symlinks and compiles for every model on this target):
//       w4a16_gemm          plain arm, B is [N, K/2],  grid (N/64,  M/64),  128 thr, 8 args
//       w4a16_gemm_t        twin arm,  B is [K/2, N],  grid (N/128, M/64),  128 thr, 9 args
//       w4a16_gemm_t_m128   twin arm,  B is [K/2, N],  grid (N/128, M/128), 128 thr, 8 args
//   from kernels/r9700/common/w4a16_gemm_rdna4.cu, when that file is present:
//       w4a16_gemm_rdna4    RDNA 4 arm, B is [N, K/2], grid (N/128, M/128), 256 thr, 8 args
//
// NOT part of the Atlas build. It lives under `scripts/scale-probe/` on
// purpose: everything in `kernels/<hw>/common/` is globbed by
// `crates/atlas-kernels/build.rs::collect_cu_files` and compiled into EVERY
// model on EVERY target, and a file that re-`#include`s two kernel sources
// would put a second copy of `w4a16_gemm` in a second module in every one of
// those builds. A probe object is not a shipped kernel.
//
// ═══════════════════════════════════════════════════════════════════════════
// BUILD: on the R9700 box, from the repository root
// ═══════════════════════════════════════════════════════════════════════════
//   SCALE_HOME=${SCALE_HOME:-/opt/scale}        # the dir holding targets/
//
//   # 1. the device object. These are the EXACT flags
//   #    crates/atlas-kernels/build_target.rs::ScaleTarget::compile passes,
//   #    plus kernels/gb10/common/KERNEL.toml [build] extra_nvcc_flags and
//   #    kernels/r9700/HARDWARE.toml [build] extra_nvcc_flags, so the object
//   #    is compiled the way the serve binary's is.
//   "$SCALE_HOME/targets/gfx1201/bin/nvcc" \
//       --cuda-device-only -c -O3 \
//       --fmad=false -DTQ_PLUS_SIGNS -ffp-contract=off \
//       scripts/scale-probe/w4a16_gemm_bench.cu \
//       -o /tmp/w4a16_gemm_bench.o
//
//   # 2. the host driver (plain CUDA driver API; SCALE ships libcuda)
//   g++ -O2 -std=c++17 scripts/scale-probe/w4a16_bench.cpp \
//       -o /tmp/w4a16_bench \
//       -I"$SCALE_HOME/include" -L"$SCALE_HOME/lib" \
//       -Wl,-rpath,"$SCALE_HOME/lib" -lcuda -lnuma
//
//   # 3. run
//   /tmp/w4a16_bench --object /tmp/w4a16_gemm_bench.o
//
// Resource footprint of each symbol, which is the OTHER half of the A/B and
// costs no run at all (PREFILL-ANALYSIS.md §4 S1 calls for exactly this):
//   llvm-readelf --notes /tmp/w4a16_gemm_bench.o | grep -iE 'vgpr|scratch|occupancy'
//   # or: roc-obj-ls /tmp/w4a16_gemm_bench.o
// A non-zero ScratchSize on `w4a16_gemm_t_m128` and zero on `w4a16_gemm` is
// suspect S1 confirmed outright.

#include "../../kernels/gb10/qwen3.6-27b/nvfp4/w4a16_gemm.cu"

// `__has_include` so this object still builds before the RDNA 4 kernel lands,
// and so a checkout without it measures the three existing arms rather than
// failing to compile.
#if __has_include("../../kernels/r9700/common/w4a16_gemm_rdna4.cu")
#include "../../kernels/r9700/common/w4a16_gemm_rdna4.cu"
#endif
