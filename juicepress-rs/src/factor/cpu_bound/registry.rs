use super::cpu_factors;
use super::details::*;
use super::factor::*;
use crate::FileObject;
use std::sync::Arc;

pub trait CPUFactor: Send + Sync {
    fn calculate(&self, file_object: &FileObject) -> Option<(f64, Details)>;
    fn weight(&self) -> f64;
    fn key(&self) -> String;
}

cpu_factors!(Filename, BinaryString, TaintSymbol);
