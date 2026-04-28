use serde::Deserialize;

use super::io_factor_devel::*;

#[derive(Serialize)]
pub struct ManpageDetails {
    pub for_filename: String,
    pub path: String,
    pub query: String,
}

#[derive(Clone, Deserialize, Default)]
pub struct Manpage {
    #[serde(skip)]
    db: Option<Arc<PgPool>>,
}

impl Manpage {
    #[allow(unused_variables)]
    pub fn new(settings: Settings, all_objects: Vec<Arc<FileObject>>) -> Self {
        Self {
            db: settings.pg_pool,
        }
    }

    async fn pkg_exists(&self, file_name: &str) -> Result<String, sqlx::Error> {
        let ilike = format!("{}.%", &file_name);
        let qry_result = sqlx::query!(
                r"SELECT location, file_name FROM ubuntu_file WHERE location ~* '^usr/share/man/' and file_name like $1",
            &ilike
        )
        .fetch_one(self.db.clone().unwrap().as_ref())
        .await?;

        let path = format!("{}/{}", &qry_result.location, &qry_result.file_name);

        Ok(path)
    }
}

impl IOFactor for Manpage {
    async fn calculate(&self, file_object: Arc<FileObject>) -> Option<(f64, Details)> {
        let file_name = file_object.sanitized_filename.replace(".so", "");

        let path = self.pkg_exists(&file_name).await.unwrap_or_default();

        let query = format!(
            r"SELECT location, file_name FROM ubuntu_file WHERE location ~* '^usr/share/man/' and file_name LIKE '{}.%'",
            file_name
        );

        let mut result = 1.0;
        let mut details = Details::None;

        if path != "" {
            result = 0.0;
            details = Details::Manpage(ManpageDetails {
                path,
                for_filename: file_name.into(),
                query,
            });
        }
        Some((result, details))
    }

    fn key(&self) -> String {
        "not_in_ubuntu_manpages".into()
    }

    fn weight(&self) -> f64 {
        1.0
    }
}
