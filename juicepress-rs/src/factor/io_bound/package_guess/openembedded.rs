use serde::Deserialize;

use super::package_guesser_devel::*;

#[derive(Clone, Deserialize, Default)]
pub struct OpenEmbedded {
    guesser: Guess,
}

impl OpenEmbedded {
    #[allow(unused_variables)]
    pub fn new(settings: Settings, all_objects: Vec<Arc<FileObject>>) -> Self {
        Self {
            guesser: Guess::new(
                settings.pg_pool.unwrap(),
                Arc::new(all_objects.filenames()),
                Datasource::OpenEmbedded,
            ),
        }
    }
}

impl IOFactor for OpenEmbedded {
    async fn calculate(&self, file_object: Arc<FileObject>) -> Option<(f64, Details)> {
        let pkg_guess = self.guesser.best(file_object).await;
        match pkg_guess {
            Some(guess) => Some((1.0 - guess.confidence, Details::OpenEmbedded(guess))),
            None => Some((1.0, Details::None)),
        }
    }

    fn weight(&self) -> f64 {
        1.0
    }

    fn key(&self) -> String {
        "confidence_file_not_in_openembedded_layers".to_owned()
    }
}
