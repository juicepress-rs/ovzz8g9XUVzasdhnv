macro_rules! cpu_factors {
    ($($variant:ident),* $(,)?) => {
        use clap::ValueEnum;
        use serde::Deserialize;
        use crate::Settings;

        #[derive(Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum CPUFactorEnum {
            $($variant($variant)),*
        }

        impl CPUFactor for CPUFactorEnum {

            fn calculate(&self, file_object: &FileObject) -> Option<(f64, Details)> {
                match self {
                    $(CPUFactorEnum::$variant(inner) => inner.calculate(file_object)),*
                }
            }

            fn weight(&self) -> f64 {
                match self {
                    $(CPUFactorEnum::$variant(inner) => inner.weight()),*
                }
            }

            fn key(&self) -> String {
                match self {
                    $(CPUFactorEnum::$variant(inner) => inner.key()),*
                }
            }
        }

        $(
            impl From<$variant> for CPUFactorEnum {
                fn from(v: $variant) -> Self {
                    CPUFactorEnum::$variant(v)
                }
            }
        )*

        #[derive(ValueEnum, Deserialize, Debug, Clone, Copy)]
        #[serde(rename_all = "snake_case")]
        #[value(rename_all = "snake_case")]
        pub enum CPUFactorKind {
            $($variant),*
        }

        impl CPUFactorKind {
            pub fn build(self, settings: Settings) -> CPUFactorEnum {
                match self {
                    $(CPUFactorKind::$variant => $variant::new(settings).into()),*
                }
            }
        }

        impl Default for CPUFactorKind {
            fn default() -> Self {
                cpu_factors!(@first $($variant),*)
            }
        }

    };
    (@first $first:ident $(, $rest:ident)*) => {
        CPUFactorKind::$first
    };
}

pub(crate) use cpu_factors;
