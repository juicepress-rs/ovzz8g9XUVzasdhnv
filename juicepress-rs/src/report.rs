use std::{fs::OpenOptions, io::BufWriter, sync::Arc};

use crate::FileObject;
use serde::Serialize;

#[derive(Serialize)]
pub struct Report {
    total_sec: f64,
    analysis_sec: f64,
    collection_sec: f64,
    root: String,
    file_count: usize,
    elf_count: usize,
    results: Vec<Arc<FileObject>>,
}

impl Report {
    pub fn new(
        analysis_sec: f64,
        collection_sec: f64,
        root: &String,
        file_objects: Vec<Arc<FileObject>>,
    ) -> Self {
        let only_ranked: Vec<Arc<FileObject>> = file_objects
            .iter()
            .filter(|fo| {
                let ranking = fo.ranking.0.blocking_lock();
                ranking.len() > 0
            })
            .map(Arc::clone)
            .collect();

        Report {
            total_sec: analysis_sec + collection_sec,
            root: root.to_owned(),
            analysis_sec,
            collection_sec,
            file_count: file_objects.len(),
            elf_count: only_ranked.len(),
            results: only_ranked,
        }
    }

    pub fn save(&self, to: &String) {
        if to == "-" {
            println!("{}", serde_json::to_string_pretty(&self).unwrap());
            return;
        }
        let file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(to)
            .unwrap();

        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &self).unwrap();
    }
}
