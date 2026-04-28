macro_rules! io_factors {
    ($($variant:ident),* $(,)?) => {
        use clap::ValueEnum;
        use serde::Deserialize;
        use crate::Settings;

        #[derive(Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum IOFactorEnum {
            $($variant($variant)),*
        }

        impl IOFactor for IOFactorEnum {

            async fn calculate(&self, file_object: Arc<FileObject>) -> Option<(f64, Details)> {
                match self {
                    $(IOFactorEnum::$variant(inner) => inner.calculate(file_object).await),*
                }
            }

            fn weight(&self) -> f64 {
                match self {
                    $(IOFactorEnum::$variant(inner) => inner.weight()),*
                }
            }

            fn key(&self) -> String {
                match self {
                    $(IOFactorEnum::$variant(inner) => inner.key()),*
                }
            }
        }

        $(
            impl From<$variant> for IOFactorEnum {
                fn from(v: $variant) -> Self {
                    IOFactorEnum::$variant(v)
                }
            }
        )*

        #[derive(ValueEnum, Deserialize, Debug, Clone, Copy)]
        #[serde(rename_all = "snake_case")]
        #[value(rename_all = "snake_case")]
        pub enum IOFactorKind {
            $($variant),*
        }

        impl IOFactorKind {
            pub fn build(self, settings: Settings, all_objects: Vec<Arc<FileObject>>) -> IOFactorEnum {
                match self {
                    $(IOFactorKind::$variant => $variant::new(settings, all_objects).into()),*
                }
            }
        }

        impl Default for IOFactorKind {
            fn default() -> Self {
                io_factors!(@first $($variant),*)
            }
        }

    };
    (@first $first:ident $(, $rest:ident)*) => {
        IOFactorKind::$first
    };
}

pub(crate) use io_factors;
