#![allow(dead_code)]
use super::SelectionFilter;

use crate::FileObject;
use serde::Deserialize;
use std::sync::Arc;

// add your scoring function implementations here! you need a deserializable empty struct and an impl of the
// SelectionFilter-Trait! Finally, add your struct to registry.rs.

#[derive(Deserialize)]
pub struct IsUserspaceElf;

impl SelectionFilter for IsUserspaceElf {
    fn apply(&self, fo: &Arc<FileObject>) -> bool {
        fo.userspace_elf
    }
}

#[derive(Deserialize)]
pub struct AtLeastOneKibyte;

// this is just a simple example not in use. in theory, you could define arbitrarily complex
// filters, as long as the signature fits. for example, you could...
//  - calculate byte entropy based on the fo.bytes field.
//  - access fo.finfo and collect permissions, e.g., special bits like SUID.
//  - inspect ELF segments by calling fo.parse_elf().
//  - add the parser identification algorithm.. (which of course slows this significantly down).
impl SelectionFilter for AtLeastOneKibyte {
    fn apply(&self, fo: &Arc<FileObject>) -> bool {
        fo.size >= 1024
    }
}
