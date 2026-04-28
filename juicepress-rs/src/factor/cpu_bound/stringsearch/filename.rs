use serde::Deserialize;

use super::stringsearch_devel::*;

#[derive(Clone, Deserialize, Default)]
pub struct Filename {
    #[serde(skip)]
    fuzzy: Option<FuzzySearch>,
}

// We use the MatchRanking Approach to auto-create an abbreviation. Using this algo
// makes sense because it works as follows (wiki):
// 1 Delete all vowels unless the vowel begins the word
// 2 Remove the second consonant of any double consonants present
// 3. Reduce codex to 6 letters by joining the first 3 and last 3 letters only

impl CPUFactor for Filename {
    fn calculate(&self, file_object: &FileObject) -> Option<(f64, Details)> {
        let result = self
            .fuzzy
            .clone()
            .unwrap()
            .search(&file_object.sanitized_filename)?;
        Some((result.jaro_winkler, Details::Filename(result)))
    }

    fn weight(&self) -> f64 {
        1.0
    }

    fn key(&self) -> String {
        "keyword_in_filename".to_owned()
    }
}

impl Filename {
    pub fn new(settings: Settings) -> Self {
        let search_keywords = &settings.search;
        Self {
            fuzzy: Some(FuzzySearch::new(search_keywords, 0.8, 1, true)),
        }
    }
}
