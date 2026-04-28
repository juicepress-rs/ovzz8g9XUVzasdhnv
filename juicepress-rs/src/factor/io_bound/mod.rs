mod macros;
mod manpage;
mod nsrl;
mod package_guess;
mod registry;

use macros::io_factors;

mod io_factor_devel {
    pub use super::super::Details;
    pub use super::factor::IOFactor;
    pub use crate::{FileObject, Settings};
    pub use serde::Serialize;
    pub use sqlx::postgres::{PgPool, PgPoolOptions};
    pub use std::collections::HashSet;
    pub use std::sync::Arc;
}

pub mod details {
    pub use super::super::Details;
    pub use super::manpage::ManpageDetails;
    pub use super::nsrl::NSRLDetails;
    pub use super::package_guess::details::*;
}

pub mod factor {
    pub use super::manpage::Manpage;
    pub use super::nsrl::Nsrl;
    pub use super::package_guess::factor::*;
    pub use super::registry::{IOFactor, IOFactorEnum, IOFactorKind};
}
