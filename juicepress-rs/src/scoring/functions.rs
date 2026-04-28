#![allow(dead_code)]
use super::ScoringFunction;

use crate::FileObject;
use serde::Deserialize;
use std::sync::Arc;

// add your scoring function implementations here! you need a deserializable empty struct and an impl of the
// ScoringFunction-Trait! Finally, add your struct to registry.rs.

#[derive(Deserialize)]
pub struct WeightedLinearCombination;

impl ScoringFunction for WeightedLinearCombination {
    fn score(&self, fo: &Arc<FileObject>) -> f64 {
        let ranking = fo.ranking.0.blocking_lock();
        ranking.iter().map(|(_, res)| res.result * res.weight).sum()
    }
}
