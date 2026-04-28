use std::{
    borrow::Cow,
    collections::{HashMap, HashSet},
    sync::Arc,
};

use ordered_float::OrderedFloat;
use rayon::iter::{
    IntoParallelIterator, IntoParallelRefIterator, ParallelBridge, ParallelIterator,
};
use serde::{Deserialize, Serialize};
use sqlx::{PgPool, Postgres, postgres::PgArguments};
use tokio::runtime::Runtime;

use crate::FileObject;

#[derive(Default, Clone, Deserialize)]
pub enum Datasource {
    #[default]
    Alpine,
    Buildroot,
    Ubuntu,
    OpenWrt,
    OpenEmbedded,
    PTXDist,
}

#[allow(dead_code)]
#[derive(Default, Debug, Clone, Serialize)]
pub struct PackageDetails {
    pub for_filename: Option<String>,
    pub id: i64,
    pub name: String,
    pub confidence: f64,
    pub pkg_size: f64,
    pub fw_overlap: f64,
    pub query: Option<String>,
}

#[derive(Clone, Deserialize, Default)]
pub struct Guess {
    #[serde(skip)]
    pgpool: Option<Arc<PgPool>>,
    all_file_names: Arc<HashSet<String>>,
    repository: Datasource,
}

#[allow(dead_code)]
struct DatabaseRecord {
    id: i64,
    file_name: String,
    location: String,
    package_id: i64,
    package_name: String,
}

impl Guess {
    pub fn new(
        pgpool: Arc<PgPool>,
        all_file_names: Arc<HashSet<String>>,
        repository: Datasource,
    ) -> Self {
        Self {
            pgpool: Some(pgpool),
            all_file_names,
            repository,
        }
    }

    async fn perform_query_for(&self, file_object: Arc<FileObject>) -> Vec<DatabaseRecord> {
        // you might be thinking I'm crazy, but sqlx::query_as! does not support non-static format strings. I'm not crazy.
        let dataset = match self.repository {
            Datasource::PTXDist => sqlx::query_as!(
                DatabaseRecord,
                r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM ptxdist_distrokit_file f
                JOIN ptxdist_distrokit_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM ptxdist_distrokit_file WHERE file_name=$1) AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.service)'",
                file_object.sanitized_filename
            ).fetch_all(self.pgpool.clone().unwrap().as_ref()).await,
            Datasource::OpenEmbedded => sqlx::query_as!(
                DatabaseRecord,
                r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM openembedded_file f
                JOIN openembedded_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM openembedded_file WHERE file_name=$1) AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.service)'",
                file_object.sanitized_filename
            ).fetch_all(self.pgpool.clone().unwrap().as_ref()).await,
            Datasource::Alpine => sqlx::query_as!(
                DatabaseRecord,
                r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM alpine_file f
                JOIN alpine_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM alpine_file WHERE file_name=$1) AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.service)'",
                file_object.sanitized_filename
            ).fetch_all(self.pgpool.clone().unwrap().as_ref()).await,
            Datasource::Buildroot => sqlx::query_as!(
                DatabaseRecord,
                r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM buildroot_file f
                JOIN buildroot_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM buildroot_file WHERE file_name=$1) AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.service)'",
                file_object.sanitized_filename
            ).fetch_all(self.pgpool.clone().unwrap().as_ref()).await,
            Datasource::Ubuntu => sqlx::query_as!(
                DatabaseRecord,
                r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM ubuntu_file f
                JOIN ubuntu_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM ubuntu_file WHERE file_name=$1) AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.deb$)|(\.service)|(.*[Dd][Ee][Bb][Ii][Aa][Nn].*)'",
                file_object.sanitized_filename
            ).fetch_all(self.pgpool.clone().unwrap().as_ref()).await,
            Datasource::OpenWrt => sqlx::query_as!(
                DatabaseRecord,
                r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM openwrt_file f
                JOIN openwrt_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM openwrt_file WHERE file_name=$1) AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.service)'",
                file_object.sanitized_filename
            ).fetch_all(self.pgpool.clone().unwrap().as_ref()).await,
        };
        dataset.unwrap()
    }

    fn get_query_string(&self, file_object: Arc<FileObject>) -> String {
        let kind = match self.repository {
            Datasource::Alpine => "alpine",
            Datasource::Buildroot => "buildroot",
            Datasource::Ubuntu => "ubuntu",
            Datasource::OpenWrt => "openwrt",
            Datasource::OpenEmbedded => "openembedded",
            Datasource::PTXDist => "ptxdist_distrokit",
        };
        format!(
            r"SELECT DISTINCT f.id, f.file_name, f.location, f.package_id, p.name AS package_name FROM {kind}_file f
                JOIN {kind}_pkg p ON p.id = f.package_id WHERE
                    package_id IN (SELECT DISTINCT package_id FROM {kind}_file WHERE file_name='{filename}') AND
                    f.location !~* '(usr/share.*)|(.*systemd.*)' AND
                    f.file_name !~* '(\.h$)|(\.hpp$)|(\.cpp$)|(\.c$)|(.*README.*)|(\.deb$)|(\.service)|(.*[Dd][Ee][Bb][Ii][Aa][Nn].*)'",
            kind = kind,
            filename = file_object.sanitized_filename
        )
    }

    fn create_lookup_tables<'a>(
        &self,
        dataset: &'a Vec<DatabaseRecord>,
    ) -> (HashMap<i64, HashSet<&'a str>>, HashMap<i64, &'a str>) {
        let mut file_lut: HashMap<i64, HashSet<&'a str>> = HashMap::new();
        let mut package_lut: HashMap<i64, &'a str> = HashMap::new();

        for row in dataset {
            package_lut
                .entry(row.package_id)
                .or_insert(&row.package_name.as_str());
            let pkg_files = file_lut.entry(row.package_id).or_insert_with(HashSet::new);

            pkg_files.insert(&row.file_name.as_str());
        }
        (file_lut, package_lut)
    }

    fn best_guess_from_lut(
        &self,
        file_lut: HashMap<i64, HashSet<&str>>,
        package_lut: HashMap<i64, &str>,
    ) -> Option<PackageDetails> {
        let guess: Option<PackageDetails> = file_lut
            .par_iter()
            .map(|(id, files)| {
                let fw_overlap = files
                    .par_iter()
                    .filter(|f| self.all_file_names.contains(**f))
                    .count() as f64;
                let pkg_size = files.len() as f64;
                let confidence = fw_overlap / pkg_size;
                (id, confidence, pkg_size, fw_overlap)
            })
            .max_by_key(|tpl| OrderedFloat(tpl.1))
            .map(|(id, confidence, pkg_size, fw_overlap)| PackageDetails {
                for_filename: None,
                id: *id,
                name: package_lut.get(&id).unwrap().to_string(),
                pkg_size,
                fw_overlap,
                confidence,
                query: None,
            });

        guess
    }

    pub async fn best(&self, file_object: Arc<FileObject>) -> Option<PackageDetails> {
        let dataset = self.perform_query_for(file_object.clone()).await;

        if dataset.is_empty() {
            return None;
        }

        let (file_lut, package_lut) = self.create_lookup_tables(&dataset);

        let guesses = self.best_guess_from_lut(file_lut, package_lut);

        let mut best = guesses
            .iter()
            .max_by_key(|&guess| OrderedFloat(guess.confidence))?
            .to_owned();

        best.for_filename = Some(file_object.sanitized_filename.to_owned());
        best.query = Some(self.get_query_string(file_object));
        Some(best)
    }
}
