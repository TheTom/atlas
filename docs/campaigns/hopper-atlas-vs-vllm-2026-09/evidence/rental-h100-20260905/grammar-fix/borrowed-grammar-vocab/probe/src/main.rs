// SPDX-License-Identifier: AGPL-3.0-only
// Standalone diagnostic allocator; production xgrammar remains unsafe-free.
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use xgrammar::compiler::GrammarCompiler;
use xgrammar::tokenizer::{TokenizerInfo, VocabType};

struct Counter;
static ACTIVE: AtomicBool = AtomicBool::new(false);
static ALLOCS: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        if ACTIVE.load(Ordering::Relaxed) { ALLOCS.fetch_add(1, Ordering::Relaxed); }
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        if ACTIVE.load(Ordering::Relaxed) { ALLOCS.fetch_add(1, Ordering::Relaxed); }
        unsafe { System.alloc_zeroed(layout) }
    }
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, size: usize) -> *mut u8 {
        if ACTIVE.load(Ordering::Relaxed) { ALLOCS.fetch_add(1, Ordering::Relaxed); }
        unsafe { System.realloc(ptr, layout, size) }
    }
}
#[global_allocator]
static ALLOCATOR: Counter = Counter;

fn allocations(irrelevant: usize) -> usize {
    let mut vocab: Vec<String> = (0..irrelevant)
        .map(|i| format!("z-irrelevant-token-{i:012}"))
        .collect();
    vocab.push("yes".into());
    vocab.push("<eos>".into());
    let eos = (vocab.len()-1) as i32;
    let info = TokenizerInfo::new(&vocab, VocabType::Raw, None, Some(vec![eos]), false);
    let compiler = GrammarCompiler::new(info, 1, false, -1);
    let grammar = compiler.compile_grammar_from_ebnf("root ::= \"yes\"\n", "root").unwrap();
    ALLOCS.store(0, Ordering::Relaxed);
    ACTIVE.store(true, Ordering::Relaxed);
    let states = grammar.compile_top_k_masks(512);
    ACTIVE.store(false, Ordering::Relaxed);
    let count = ALLOCS.load(Ordering::Relaxed);
    println!("irrelevant={irrelevant} states={states} allocations={count}");
    count
}

fn main() {
    let small = allocations(4096);
    let large = allocations(8192);
    assert!(large <= small,
        "cold mask preparation allocates buffers for irrelevant vocabulary: {small} -> {large}");
}
