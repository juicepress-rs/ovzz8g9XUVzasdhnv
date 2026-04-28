use std::{
    collections::{HashMap, HashSet},
    sync::Mutex,
};

use fuzzt::algorithms::{jaro_winkler, levenshtein};
use ordered_float::OrderedFloat;
use rayon::iter::{
    IntoParallelIterator, IntoParallelRefIterator, ParallelBridge, ParallelIterator,
};
use rphonetic::{Encoder, MatchRatingApproach};
use serde::Serialize;
use std::cmp::min;

#[allow(dead_code)]
#[derive(Serialize)]
pub struct FuzzyDetail {
    pub encodings: HashSet<String>,
    pub string: String,
    pub string_pure: String,
    pub matched_encoding: String,
    pub matched_window: String,
    pub jaro_winkler: f64,
    pub levenshtein: usize,
}

#[derive(Clone)]
pub struct FuzzySearch {
    encodings: HashSet<String>,
    jaro_lbound: f64,
    levenshtein_ubound: usize,
}

impl FuzzyDetail {
    pub fn create(search: &FuzzySearch, on_string: &String) -> Self {
        Self {
            encodings: search.encodings.to_owned(),
            string: on_string.to_owned(),
            string_pure: on_string.to_ascii_lowercase().to_owned(),
            jaro_winkler: 0.0,
            levenshtein: on_string.len(),
            matched_encoding: String::default(),
            matched_window: String::default(),
        }
    }
}

impl FuzzySearch {
    pub fn search(&self, on_string: &str) -> Option<FuzzyDetail> {
        let lower_str = on_string.to_ascii_lowercase();

        let mut best: Option<FuzzyDetail> = None;
        for enc in &self.encodings {
            let win_size = min(enc.len(), lower_str.len());
            for i in 0..lower_str.len() - win_size {
                let window = &lower_str[i..i + win_size];
                let j = jaro_winkler(enc, window);
                let l = levenshtein(enc, window);

                if j < self.jaro_lbound || l > self.levenshtein_ubound {
                    continue;
                }
                if best.is_none() {
                    best = Some(FuzzyDetail::create(self, &on_string.to_string()));
                }
                if let Some(ref mut b) = best
                    && b.jaro_winkler < j
                {
                    b.jaro_winkler = j;
                    b.levenshtein = l;
                    b.matched_encoding = enc.to_owned();
                    b.matched_window = window.to_owned();
                }
            }
        }

        best
    }

    pub fn new(
        search_keywords: &Vec<String>,
        jaro_lbound: f64,
        levenshtein_ubound: usize,
        generate_abbrev: bool,
    ) -> Self {
        let pure: Vec<String> = search_keywords
            .iter()
            .map(|kw| kw.to_ascii_lowercase().to_owned())
            .filter(|kw| kw.len() > 0)
            .collect();

        let mut encodings = HashSet::<String>::new();
        pure.iter().for_each(|kw| {
            encodings.insert(kw.to_owned());
            let e = MatchRatingApproach.encode(kw).to_ascii_lowercase();
            if generate_abbrev && e != "" && e.len() >= 4 {
                encodings.insert(e);
            }
        });

        Self {
            encodings,
            jaro_lbound,
            levenshtein_ubound,
        }
    }
}
