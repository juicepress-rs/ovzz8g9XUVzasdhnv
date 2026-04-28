use super::details::*;
use super::factor::*;
use super::io_factors;
use crate::FileObject;
use std::sync::Arc;

pub trait IOFactor: Send + Sync {
    fn weight(&self) -> f64;
    fn key(&self) -> String;
    async fn calculate(&self, file_object: Arc<FileObject>) -> Option<(f64, Details)>;
}

io_factors!(
    Nsrl,
    Alpine,
    Ubuntu,
    OpenWrt,
    OpenEmbedded,
    PtxDist,
    Buildroot,
    Manpage
);
