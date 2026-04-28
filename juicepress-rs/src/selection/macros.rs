macro_rules! selection_filters {
    ($($variant:ident),* $(,)?) => {
        use clap::ValueEnum;
        use serde::Deserialize;

        #[derive(Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum SelectionFilterEnum {
            $($variant($variant)),*
        }

        impl SelectionFilter for SelectionFilterEnum {
            fn apply(&self, fo: &Arc<FileObject>) -> bool {
                match self {
                    $(SelectionFilterEnum::$variant(inner) => inner.apply(fo)),*
                }
            }
        }

        $(
            impl From<$variant> for SelectionFilterEnum {
                fn from(v: $variant) -> Self {
                    SelectionFilterEnum::$variant(v)
                }
            }
        )*

        #[derive(ValueEnum, Deserialize, Debug, Clone, Copy)]
        #[serde(rename_all = "snake_case")]
        #[value(rename_all = "snake_case")]
        pub enum SelectionFilterKind {
            $($variant),*
        }

        impl From<SelectionFilterKind> for SelectionFilterEnum {
            fn from(kind: SelectionFilterKind) -> Self {
                match kind {
                    $(SelectionFilterKind::$variant => $variant.into()),*
                }
            }
        }

        impl Default for SelectionFilterKind {
            fn default() -> Self {
                selection_filters!(@first $($variant),*)
            }
        }

        impl Default for SelectionFilterEnum {
            fn default() -> Self {
                SelectionFilterKind::default().into()
            }
        }
    };
    (@first $first:ident $(, $rest:ident)*) => {
        SelectionFilterKind::$first
    };
}

pub(crate) use selection_filters;
