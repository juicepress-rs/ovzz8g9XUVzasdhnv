mod alpine;
mod buildroot;
mod common;
mod openembedded;
mod openwrt;
mod ptxdist;
mod ubuntu;

use super::registry;

mod package_guesser_devel {
    pub use super::super::io_factor_devel::*;
    pub use super::common::*;
    pub use crate::FileNameExt;
}

pub mod details {
    pub use super::super::details::Details;
    pub use super::common::PackageDetails;
}

// add your package guesser factors here
pub mod factor {
    pub use super::alpine::Alpine;
    pub use super::buildroot::Buildroot;
    pub use super::openembedded::OpenEmbedded;
    pub use super::openwrt::OpenWrt;
    pub use super::ptxdist::PtxDist;
    pub use super::registry::{IOFactor, IOFactorEnum};
    pub use super::ubuntu::Ubuntu;
}
