use super::functions::*;
use super::scorings;
use crate::FileObject;
use std::sync::Arc;

pub trait ScoringFunction {
    fn score(&self, fo: &Arc<FileObject>) -> f64;
}

scorings!(
    WeightedLinearCombination,
    // add your scoring here!
);
