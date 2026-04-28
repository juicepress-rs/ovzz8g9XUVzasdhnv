use super::stringsearch_devel::*;
use extract_strings::AsciiStrings;
use serde::Deserialize;

use ordered_float::OrderedFloat;

#[derive(Clone, Deserialize, Default)]
pub struct BinaryString {
    #[serde(skip)]
    fuzzy: Option<FuzzySearch>,
}

impl CPUFactor for BinaryString {
    fn calculate(&self, file_object: &FileObject) -> Option<(f64, Details)> {
        let best: FuzzyDetail = file_object
            .bytes
            .as_slice()
            .iter_ascii_strings(3)
            .map(|s| self.fuzzy.clone().unwrap().search(&s))
            .flatten()
            .max_by_key(|fres| OrderedFloat(fres.jaro_winkler))?;

        Some((best.jaro_winkler, Details::BinaryString(best)))
    }

    fn weight(&self) -> f64 {
        1.0
    }

    fn key(&self) -> String {
        "keyword_in_binary".to_owned()
    }
}

impl BinaryString {
    pub fn new(settings: Settings) -> Self {
        let search_keywords = &settings.search;
        Self {
            fuzzy: Some(FuzzySearch::new(search_keywords, 0.9, 1, true)),
        }
    }
}
