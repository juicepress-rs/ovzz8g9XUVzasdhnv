use super::filters::*;
use super::selection_filters;
use crate::FileObject;
use std::sync::Arc;

pub trait SelectionFilter {
    fn apply(&self, fo: &Arc<FileObject>) -> bool;
}

selection_filters!(
    IsUserspaceElf,
    AtLeastOneKibyte,
    // add your scoring here!
);
