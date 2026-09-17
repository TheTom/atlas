// SPDX-License-Identifier: AGPL-3.0-only

//! GDN prefill ops — extracted from `ssm_gdn_a.rs` during the ≤500-line split.
//! All public items remain available at `crate::layers::ops::*` via the
//! re-export in `ops.rs`.

#![allow(unused_imports)]

use anyhow::Result;
use spark_runtime::gpu::{DevicePtr, GpuBackend, KernelHandle};
use spark_runtime::kernel_args::{KernelLaunch, div_ceil};

use crate::layers::moe;
use crate::weight_map::{DenseWeight, Fp8DenseWeight, Fp8Weight, QuantizedWeight};

use super::*;

/// Gated delta rule prefill (multi-token, sequential SSM update within kernel).
///
/// Processes `seq_len` tokens sequentially per (batch, head) pair.
/// Supports strided access: Q/K/V/gate/beta may have different strides
/// between tokens (e.g., from conv1d output with interleaved Q|K|V layout).
///
/// Kernel: `gated_delta_rule_prefill(h_state, query, key, value,
///          gate, beta, output, batch_size, seq_len, num_k_heads,
///          num_v_heads, k_dim, v_dim, qk_stride, v_stride, gb_stride)`
/// Grid: (num_v_heads, batch, 1)  Block: (128, 1, 1)
#[allow(clippy::too_many_arguments)]
pub fn gdn_prefill(
    gpu: &dyn GpuBackend,
    kernel: KernelHandle,
    h_state: DevicePtr,
    query: DevicePtr,
    key: DevicePtr,
    value: DevicePtr,
    gate: DevicePtr,
    beta: DevicePtr,
    output: DevicePtr,
    batch_size: u32,
    seq_len: u32,
    num_k_heads: u32,
    num_v_heads: u32,
    k_dim: u32,
    v_dim: u32,
    qk_stride: u32,
    v_stride: u32,
    gb_stride: u32,
    stream: u64,
) -> Result<()> {
    KernelLaunch::new(gpu, kernel)
        .grid([num_v_heads, batch_size, 1])
        .block([128, 1, 1])
        .shared_mem(4 * k_dim * 4) // double-buffered k[128]+q[128] × 2 buffers × 4 bytes
        .arg_ptr(h_state)
        .arg_ptr(query)
        .arg_ptr(key)
        .arg_ptr(value)
        .arg_ptr(gate)
        .arg_ptr(beta)
        .arg_ptr(output)
        .arg_u32(batch_size)
        .arg_u32(seq_len)
        .arg_u32(num_k_heads)
        .arg_u32(num_v_heads)
        .arg_u32(k_dim)
        .arg_u32(v_dim)
        .arg_u32(qk_stride)
        .arg_u32(v_stride)
        .arg_u32(gb_stride)
        .launch(stream)
}

/// Split-v_dim prefill: 2 CTAs per v-head, 64 threads each.
///
/// Kernel: `gated_delta_rule_prefill_split(h_state, query, key, value,
///          gate, beta, output, batch_size, seq_len, num_k_heads,
///          num_v_heads, k_dim, v_dim, qk_stride, v_stride, gb_stride)`
/// Grid: (num_v_heads * 2, batch, 1)  Block: (64, 1, 1)
#[allow(clippy::too_many_arguments)]
pub fn gdn_prefill_split(
    gpu: &dyn GpuBackend,
    kernel: KernelHandle,
    h_state: DevicePtr,
    query: DevicePtr,
    key: DevicePtr,
    value: DevicePtr,
    gate: DevicePtr,
    beta: DevicePtr,
    output: DevicePtr,
    batch_size: u32,
    seq_len: u32,
    num_k_heads: u32,
    num_v_heads: u32,
    k_dim: u32,
    v_dim: u32,
    qk_stride: u32,
    v_stride: u32,
    gb_stride: u32,
    stream: u64,
) -> Result<()> {
    KernelLaunch::new(gpu, kernel)
        .grid([num_v_heads * 2, batch_size, 1])
        .block([64, 1, 1])
        .shared_mem(4 * k_dim * 4) // double-buffered k[K_DIM]+q[K_DIM] × 2 buffers × 4 bytes
        .arg_ptr(h_state)
        .arg_ptr(query)
        .arg_ptr(key)
        .arg_ptr(value)
        .arg_ptr(gate)
        .arg_ptr(beta)
        .arg_ptr(output)
        .arg_u32(batch_size)
        .arg_u32(seq_len)
        .arg_u32(num_k_heads)
        .arg_u32(num_v_heads)
        .arg_u32(k_dim)
        .arg_u32(v_dim)
        .arg_u32(qk_stride)
        .arg_u32(v_stride)
        .arg_u32(gb_stride)
        .launch(stream)
}

/// 4-way split prefill: 4 CTAs per v-head, 32 threads each (128 total CTAs).
///
/// Kernel: `gated_delta_rule_prefill_split4(h_state, query, key, value,
///          gate, beta, output, batch_size, seq_len, num_k_heads,
///          num_v_heads, k_dim, v_dim, qk_stride, v_stride, gb_stride)`
/// Grid: (num_v_heads * 4, batch, 1)  Block: (32, 1, 1)
///
/// # A wider split is NOT a launch-parameter change
///
/// `PREFILL-ANALYSIS.md` section 4, suspect S5, is right that this grid is
/// the largest structural regression against NVIDIA in the SCALE prefill
/// path: on gfx1201 it is 128 CTAs of ONE wave32 each on 128 SIMDs, 1 wave
/// per SIMD against a 12-wave budget, with no co-resident wave to hide an LDS
/// or global latency. Its cheapest proposed fix, "widen the split: `split8`
/// or `split16` ... the only change is the `tid` arithmetic and the grid,
/// 4 to 6 h, low risk": does not survive contact with the kernel, so this
/// note is here rather than that change.
///
/// The split is over `v_dim`, not over work. `gated_delta_rule.cu` computes
/// `tid = split * blockDim.x + threadIdx.x` and gives each thread ONE v
/// column, with that column's whole `H_reg[K_DIM]` state in registers. So
/// `num_splits * blockDim.x` must equal `v_dim`, which is 128, and
/// `split4 x 32` already spends every lane. `split8` therefore means 8 CTAs
/// of SIXTEEN threads, and two things follow:
///
///   * The smem staging is hardcoded to four loads at stride `quarter =
///     blockDim.x`, covering `K_DIM = 128` only while `blockDim.x == 32`. At
///     16 it covers 64 of 128. That is a kernel edit, in three places.
///   * A 16-thread block still occupies a full wave32 slot with half its
///     lanes masked. Resident WAVES double and resident WORK does not, so the
///     8 CTAs run the same 128 lanes of arithmetic across twice the wave
///     slots. On this part that is a pessimisation, not a fix.
///
/// Splitting `K` instead of `v_dim` would add parallelism, but `hk_dot` and
/// `q_dot` are full reductions over `K_DIM` per token and `H` is updated in
/// place from them, so it needs a cross-CTA reduction and a shared `H`, a
/// different algorithm, which is what the chunked FLA path already is.
///
/// Also worth stating: section 3.3 brackets this whole kernel at 26 ms to
/// 133 ms for a 2973-token 9B prefill, i.e. 0.1% to 0.35% of the measured
/// 38.5 s TTFT. It is ranked fifth for that reason and it cannot move TTFT
/// until the projection GEMMs do. `SSM prefill [gdn_prefill]` under
/// `ATLAS_PROFILE=1` is the measurement that would overturn the estimate.
#[allow(clippy::too_many_arguments)]
pub fn gdn_prefill_split4(
    gpu: &dyn GpuBackend,
    kernel: KernelHandle,
    h_state: DevicePtr,
    query: DevicePtr,
    key: DevicePtr,
    value: DevicePtr,
    gate: DevicePtr,
    beta: DevicePtr,
    output: DevicePtr,
    batch_size: u32,
    seq_len: u32,
    num_k_heads: u32,
    num_v_heads: u32,
    k_dim: u32,
    v_dim: u32,
    qk_stride: u32,
    v_stride: u32,
    gb_stride: u32,
    stream: u64,
) -> Result<()> {
    KernelLaunch::new(gpu, kernel)
        .grid([num_v_heads * 4, batch_size, 1])
        .block([32, 1, 1])
        .shared_mem(4 * k_dim * 4) // double-buffered k[K_DIM]+q[K_DIM] × 2 buffers × 4 bytes
        .arg_ptr(h_state)
        .arg_ptr(query)
        .arg_ptr(key)
        .arg_ptr(value)
        .arg_ptr(gate)
        .arg_ptr(beta)
        .arg_ptr(output)
        .arg_u32(batch_size)
        .arg_u32(seq_len)
        .arg_u32(num_k_heads)
        .arg_u32(num_v_heads)
        .arg_u32(k_dim)
        .arg_u32(v_dim)
        .arg_u32(qk_stride)
        .arg_u32(v_stride)
        .arg_u32(gb_stride)
        .launch(stream)
}

/// Persistent GDN prefill — h_state stays in shared memory for entire sequence.
///
/// Same parameters as gdn_prefill_split4 but uses persistent CTAs with
/// 128 threads and 67 KB shared memory. Each CTA processes ALL tokens for
/// one v_head, keeping h_state in shared memory (never written to global
/// until the end). Targets L2 bandwidth (~3 TB/s) instead of LPDDR5X (273 GB/s).
///
/// Grid: (num_v_heads, batch, 1)  Block: (128, 1, 1)
/// Shared: k_dim*v_dim*4 + 4*k_dim*4 bytes
#[allow(clippy::too_many_arguments)]
pub fn gdn_prefill_persistent(
    gpu: &dyn GpuBackend,
    kernel: KernelHandle,
    h_state: DevicePtr,
    query: DevicePtr,
    key: DevicePtr,
    value: DevicePtr,
    gate: DevicePtr,
    beta: DevicePtr,
    output: DevicePtr,
    batch_size: u32,
    seq_len: u32,
    num_k_heads: u32,
    num_v_heads: u32,
    k_dim: u32,
    v_dim: u32,
    qk_stride: u32,
    v_stride: u32,
    gb_stride: u32,
    stream: u64,
) -> Result<()> {
    let smem = k_dim * v_dim * 4 + 4 * k_dim * 4; // h_state + double-buffered k/q
    KernelLaunch::new(gpu, kernel)
        .grid([num_v_heads, batch_size, 1])
        .block([128, 1, 1])
        .shared_mem(smem)
        .arg_ptr(h_state)
        .arg_ptr(query)
        .arg_ptr(key)
        .arg_ptr(value)
        .arg_ptr(gate)
        .arg_ptr(beta)
        .arg_ptr(output)
        .arg_u32(batch_size)
        .arg_u32(seq_len)
        .arg_u32(num_k_heads)
        .arg_u32(num_v_heads)
        .arg_u32(k_dim)
        .arg_u32(v_dim)
        .arg_u32(qk_stride)
        .arg_u32(v_stride)
        .arg_u32(gb_stride)
        .launch(stream)
}

/// Persistent GDN prefill with explicit shared memory size.
/// Used for WY4-persistent variant which needs more shared memory.
#[allow(clippy::too_many_arguments)]
pub fn gdn_prefill_persistent_smem(
    gpu: &dyn GpuBackend,
    kernel: KernelHandle,
    h_state: DevicePtr,
    query: DevicePtr,
    key: DevicePtr,
    value: DevicePtr,
    gate: DevicePtr,
    beta: DevicePtr,
    output: DevicePtr,
    batch_size: u32,
    seq_len: u32,
    num_k_heads: u32,
    num_v_heads: u32,
    k_dim: u32,
    v_dim: u32,
    qk_stride: u32,
    v_stride: u32,
    gb_stride: u32,
    smem: u32,
    stream: u64,
) -> Result<()> {
    KernelLaunch::new(gpu, kernel)
        .grid([num_v_heads, batch_size, 1])
        .block([128, 1, 1])
        .shared_mem(smem)
        .arg_ptr(h_state)
        .arg_ptr(query)
        .arg_ptr(key)
        .arg_ptr(value)
        .arg_ptr(gate)
        .arg_ptr(beta)
        .arg_ptr(output)
        .arg_u32(batch_size)
        .arg_u32(seq_len)
        .arg_u32(num_k_heads)
        .arg_u32(num_v_heads)
        .arg_u32(k_dim)
        .arg_u32(v_dim)
        .arg_u32(qk_stride)
        .arg_u32(v_stride)
        .arg_u32(gb_stride)
        .launch(stream)
}
