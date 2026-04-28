mod macros;
mod registry;
mod stringsearch;

use macros::cpu_factors;

mod cpu_factor_devel {
    pub use super::super::Details;
    pub use super::factor::CPUFactor;
    pub use crate::{FileObject, Settings};
    pub use serde::Serialize;
    pub use sqlx::postgres::{PgPool, PgPoolOptions};
    pub use std::collections::HashSet;
    pub use std::sync::Arc;
}

pub mod details {
    pub use super::super::Details;
    pub use super::stringsearch::details::*;
}

pub mod factor {
    pub use super::registry::{CPUFactor, CPUFactorEnum, CPUFactorKind};
    pub use super::stringsearch::factor::*;
}
