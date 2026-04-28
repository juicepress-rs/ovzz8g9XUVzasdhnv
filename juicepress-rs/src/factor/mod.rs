#![allow(unused_imports)]

mod cpu_bound;
mod io_bound;
mod result;

pub use cpu_bound::factor::*;
pub use io_bound::factor::*;

pub use result::{Details, FactorResult};

pub mod details {
    pub use super::cpu_bound::details::*;
    pub use super::io_bound::details::*;
}

pub mod factor {
    pub use super::cpu_bound::factor::*;
    pub use super::io_bound::factor::*;
}
