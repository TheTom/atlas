// SPDX-License-Identifier: AGPL-3.0-only

use std::sync::Arc;
use super::EarleyParser;
use crate::grammar::functor::{GrammarNormalizer, GrammarOptimizer};
use crate::grammar::parse_ebnf_default;

fn parser() -> EarleyParser {
    let grammar = parse_ebnf_default("root ::= [a-z]+\n").unwrap();
    let grammar = GrammarOptimizer::apply(GrammarNormalizer::apply(grammar));
    EarleyParser::from_grammar(Arc::new(grammar))
}

#[test]
fn trial_advance_retains_scanable_scratch_and_rollback_state() {
    let mut parser = parser();
    parser.to_be_added.reserve(64);
    let allocation = parser.to_be_added.as_ptr();
    let capacity = parser.to_be_added.capacity();
    let before = parser.latest_scanable_states().to_vec();
    for byte in b'a'..=b'z' {
        assert!(parser.advance(byte));
        assert_eq!(parser.to_be_added.capacity(), capacity, "trial byte discarded reusable state scratch");
        assert_eq!(parser.to_be_added.as_ptr(), allocation);
        assert!(parser.is_completed());
        parser.pop_last_states(1);
        assert_eq!(parser.latest_scanable_states(), before);
        assert!(!parser.is_completed());
    }
    assert!(!parser.advance(b'!'));
    assert_eq!(parser.latest_scanable_states(), before);
}

#[test]
fn reset_expansion_retains_scanable_scratch() {
    let mut parser = parser();
    parser.to_be_added.reserve(64);
    let allocation = parser.to_be_added.as_ptr();
    let capacity = parser.to_be_added.capacity();
    assert!(parser.advance(b'a'));
    parser.reset();
    assert_eq!(parser.to_be_added.capacity(), capacity, "root expansion discarded reusable state scratch");
    assert_eq!(parser.to_be_added.as_ptr(), allocation);
    assert!(!parser.is_completed());
    assert!(parser.advance(b'z'));
    assert!(parser.is_completed());
}
