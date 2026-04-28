use super::details::*;
use super::factor::*;
use serde::Serialize;

#[derive(Serialize, Default)]
#[serde(untagged)]
pub enum Details {
    #[default]
    None,
    NSRL(NSRLDetails),
    Alpine(PackageDetails),
    Buildroot(PackageDetails),
    Ubuntu(PackageDetails),
    OpenWrt(PackageDetails),
    OpenEmbedded(PackageDetails),
    PTXDist(PackageDetails),
    Manpage(ManpageDetails),
    Filename(FuzzyDetail),
    BinaryString(FuzzyDetail),
    TaintSymbol(TaintSymbolResultDetails),
}

#[derive(Serialize)]
pub struct FactorResult {
    pub exec_secs: f64,
    pub result: f64,
    pub weight: f64,
    pub details: Option<Details>,
}
