use serde::Deserialize;

use super::io_factor_devel::*;

#[derive(Serialize)]
pub struct NSRLDetails {
    pub for_filename: String,
    pub nsrl_file_id: i64,
    pub query: String,
}

#[derive(Clone, Deserialize, Default)]
pub struct Nsrl {
    #[serde(skip)]
    db: Option<Arc<PgPool>>,
}

impl Nsrl {
    #[allow(unused_variables)]
    pub fn new(settings: Settings, all_objects: Vec<Arc<FileObject>>) -> Self {
        Self {
            db: settings.pg_pool,
        }
    }

    async fn pkg_exists(&self, file_name: &str) -> Result<i64, sqlx::Error> {
        let qry_result = sqlx::query!(
            r"SELECT file_id FROM nsrl_file WHERE file_name = $1",
            file_name
        )
        .fetch_one(self.db.clone().unwrap().as_ref())
        .await?;

        Ok(qry_result.file_id)
    }
}

impl IOFactor for Nsrl {
    async fn calculate(&self, file_object: Arc<FileObject>) -> Option<(f64, Details)> {
        let file_name = &file_object.sanitized_filename;

        let nsrl_file_id = self.pkg_exists(&file_name).await.unwrap_or(-1);

        let mut result = 1.0;
        let mut details = Details::None;

        if nsrl_file_id >= 0 {
            result = 0.0;
            details = Details::NSRL(NSRLDetails {
                for_filename: file_name.to_string(),
                nsrl_file_id,
                query: format!(
                    "SELECT file_id FROM nsrl_file WHERE file_name = '{}'",
                    &file_name
                ),
            });
        }

        Some((result, details))
    }

    fn key(&self) -> String {
        "file_not_in_nsrl".into()
    }

    fn weight(&self) -> f64 {
        1.0
    }
}
