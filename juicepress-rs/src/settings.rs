use crate::factor::{CPUFactorKind, IOFactorKind};
use crate::scoring::ScoringFunctionKind;
use crate::selection::SelectionFilterKind;
use clap::{Parser, ValueEnum};
use config::{Config, ConfigError, File, FileFormat};
use serde::Deserialize;
use sqlx::PgPool;
use sqlx::postgres::PgPoolOptions;
use std::path::Path;
use std::sync::Arc;
use tokio::runtime::Runtime;

#[derive(Parser, Debug, Clone)]
#[command(
    version,
    about,
    long_about = "JuicePress -- A preprocessor framework to prioritize analysis targets for vulnerability research in unpacked binary Linux firmware images.. and science!"
)]
pub struct Args {
    #[arg(short, long, help = "Path to input file tree root directory.")]
    pub path: String,
    #[arg(short, long, help = "Path to output json report.")]
    pub output: String,
    #[arg(long, num_args = 0.., help = "Keyword search arguments for some factors. Specify multiple as needed")]
    pub search: Option<Vec<String>>,
    #[arg(
        long,
        help = "Path to config.yml. Config directives are overwritten by cli arguments"
    )]
    pub config: Option<String>,
    #[arg(
        long,
        help = "Postgresql connection pool size. Default: (NUM_CPU * 2) - 1"
    )]
    pub pg_size: Option<u32>,
    #[arg(
        long,
        help = "Postgresql connection uri. Default: 'postgresql://juicepress:juicepress@127.0.0.1:2345/juicepress'"
    )]
    pub pg_uri: Option<String>,
    #[arg(
        long,
        value_enum,
        help = "Prioritization scoring function. Default: 'weighted_linear_combination'"
    )]
    pub scoring: Option<ScoringFunctionKind>,
    #[arg(long, num_args = 0.., help = "Selection phase filters. Specify multiple as needed. Default: 'is_userspace_elf'")]
    pub selection: Option<Vec<SelectionFilterKind>>,
    #[arg(long, num_args = 0.., help = "CPU-bound scoring factors for the prioritization. Specify multiple as needed. Default: ALL")]
    pub cfactor: Option<Vec<CPUFactorKind>>,
    #[arg(long, num_args = 0.., help = "IO-bound scoring factors for the prioritization. Specify multiple as needed. Default: ALL")]
    pub iofactor: Option<Vec<IOFactorKind>>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Settings {
    pub path: String,
    pub search: Vec<String>,
    pub output: String,
    pub pg_size: u32,
    pub pg_uri: String,
    #[serde(default)]
    pub scoring: ScoringFunctionKind,
    pub selection: Vec<SelectionFilterKind>,
    pub cfactor: Vec<CPUFactorKind>,
    pub iofactor: Vec<IOFactorKind>,

    #[serde(skip)]
    pub runtime_async: Option<Arc<Runtime>>,
    #[serde(skip)]
    pub pg_pool: Option<Arc<PgPool>>,
}

impl Settings {
    /// args > config file > defaults
    pub fn new() -> Result<Self, ConfigError> {
        let args = Args::parse();

        let mut builder = Config::builder();
        builder = builder
            .set_default("path", args.path)?
            .set_default("output", args.output)?
            .set_default("pg_size", (num_cpus::get() as u32) * 2)?
            .set_default(
                "pg_uri",
                "postgres://juicepress:juicepress@127.0.0.1:2345/juicepress",
            )?
            .set_default("search", Vec::<String>::new())?
            .set_default(
                "scoring",
                ScoringFunctionKind::default()
                    .to_possible_value()
                    .unwrap()
                    .get_name(),
            )?
            .set_default(
                "selection",
                vec![
                    SelectionFilterKind::default()
                        .to_possible_value()
                        .unwrap()
                        .get_name(),
                ],
            )?
            .set_default(
                "cfactor",
                CPUFactorKind::value_variants()
                    .iter()
                    .map(|c| c.to_possible_value().unwrap().get_name().to_owned())
                    .collect::<Vec<String>>(),
            )?
            .set_default(
                "iofactor",
                IOFactorKind::value_variants()
                    .iter()
                    .map(|i| i.to_possible_value().unwrap().get_name().to_owned())
                    .collect::<Vec<String>>(),
            )?;

        if let Some(cfg_path) = args.config {
            builder = builder.add_source(
                File::from(Path::new(&cfg_path))
                    .format(FileFormat::Yaml)
                    .required(true),
            );
        } else {
            // no config_path? search juicepress.yaml in common locations
            builder = builder.add_source(
                File::with_name("juicepress")
                    .format(FileFormat::Yaml)
                    .required(false),
            );
        }

        // cli overrides :)
        builder = builder
            .set_override_option("pg_size", args.pg_size)?
            .set_override_option("pg_uri", args.pg_uri)?
            .set_override_option("search", args.search)?;

        if let Some(s) = args.selection {
            builder = builder.set_override_option(
                "selection",
                Some(
                    s.iter()
                        .map(|s| s.to_possible_value().unwrap().get_name().to_owned())
                        .collect::<Vec<String>>(),
                ),
            )?;
        }

        if let Some(c) = args.cfactor {
            builder = builder.set_override_option(
                "cfactor",
                Some(
                    c.iter()
                        .map(|s| s.to_possible_value().unwrap().get_name().to_owned())
                        .collect::<Vec<String>>(),
                ),
            )?;
        }

        if let Some(i) = args.iofactor {
            builder = builder.set_override_option(
                "iofactor",
                Some(
                    i.iter()
                        .map(|x| x.to_possible_value().unwrap().get_name().to_owned())
                        .collect::<Vec<String>>(),
                ),
            )?;
        }

        if let Some(s) = args.scoring {
            builder = builder
                .set_override_option("scoring", Some(s.to_possible_value().unwrap().get_name()))?;
        }

        let config = builder.build()?;
        let mut settings = config.try_deserialize::<Settings>()?;
        Self::postgres_connect(&mut settings);
        Ok(settings)
    }

    fn postgres_connect(settings: &mut Settings) {
        let runtime = Arc::from(Runtime::new().expect("could not spawn tokio runtime"));
        let pgpool = Arc::from(
            runtime
                .block_on(
                    PgPoolOptions::default()
                        .max_connections(settings.pg_size)
                        .connect(settings.pg_uri.as_str()),
                )
                .expect("database connection error"),
        );

        settings.pg_pool = Some(pgpool);
        settings.runtime_async = Some(runtime);
    }
}
