macro_rules! scorings {
    ($($variant:ident),* $(,)?) => {
        use clap::ValueEnum;
        use serde::Deserialize;

        #[derive(Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum ScoringFunctionEnum {
            $($variant($variant)),*
        }

        impl ScoringFunction for ScoringFunctionEnum {
            fn score(&self, fo: &Arc<FileObject>) -> f64 {
                match self {
                    $(ScoringFunctionEnum::$variant(inner) => inner.score(fo)),*
                }
            }
        }

        $(
            impl From<$variant> for ScoringFunctionEnum {
                fn from(v: $variant) -> Self {
                    ScoringFunctionEnum::$variant(v)
                }
            }
        )*

        #[derive(ValueEnum, Deserialize, Debug, Clone, Copy)]
        #[serde(rename_all = "snake_case")]
        #[value(rename_all = "snake_case")]
        pub enum ScoringFunctionKind {
            $($variant),*
        }

        impl From<ScoringFunctionKind> for ScoringFunctionEnum {
            fn from(kind: ScoringFunctionKind) -> Self {
                match kind {
                    $(ScoringFunctionKind::$variant => $variant.into()),*
                }
            }
        }

        impl Default for ScoringFunctionKind {
            fn default() -> Self {
                scorings!(@first $($variant),*)
            }
        }

        impl Default for ScoringFunctionEnum {
            fn default() -> Self {
                ScoringFunctionKind::default().into()
            }
        }
    };
    (@first $first:ident $(, $rest:ident)*) => {
        ScoringFunctionKind::$first
    };
}

pub(crate) use scorings;
