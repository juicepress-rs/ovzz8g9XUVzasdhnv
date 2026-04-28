use futures::stream::FuturesUnordered;
use rayon::iter::{IntoParallelRefIterator, ParallelIterator};
use std::{sync::Arc, time::Instant};

use crate::factor::*;
use crate::scoring::{ScoringFunction, ScoringFunctionEnum};
use crate::selection::{SelectionFilter, SelectionFilterEnum};
use crate::{FileObject, Settings};

#[allow(unused_attributes)]
pub struct Scheduler {
    settings: Settings,
    scoring_function: ScoringFunctionEnum,

    file_objects: Vec<Arc<FileObject>>,

    selection_filters: Vec<SelectionFilterEnum>,
    cpu_factors: Vec<Arc<CPUFactorEnum>>,
    io_factors: Vec<Arc<IOFactorEnum>>,
}

impl Scheduler {
    pub fn new(settings: &Settings, file_objects: &Vec<Arc<FileObject>>) -> Self {
        let mut sched = Self {
            settings: settings.clone(),
            scoring_function: settings.scoring.into(),
            selection_filters: vec![],
            cpu_factors: vec![],
            io_factors: vec![],
            file_objects: file_objects.clone(),
        };

        sched.initialize();

        sched
    }

    fn initialize(&mut self) {
        self.load_selection_filters();
        self.load_cpu_factors();
        self.load_io_factors();
    }

    fn load_selection_filters(&mut self) {
        self.selection_filters = self
            .settings
            .selection
            .iter()
            .map(|s| s.clone().into())
            .collect();
    }

    fn load_cpu_factors(&mut self) {
        self.cpu_factors = self
            .settings
            .cfactor
            .iter()
            .map(|s| s.build(self.settings.clone()))
            .map(Arc::new)
            .collect();
    }

    fn load_io_factors(&mut self) {
        self.io_factors = self
            .settings
            .iofactor
            .iter()
            .map(|s| s.build(self.settings.clone(), self.file_objects.clone()))
            .map(Arc::new)
            .collect();
    }

    fn run_cpu_factors(&self, file_objects: &mut Vec<Arc<FileObject>>) {
        file_objects.par_iter().for_each(|file_object| {
            self.cpu_factors.iter().for_each(|factor| {
                let ts = Instant::now();
                let (value, details) = factor.calculate(file_object).unwrap_or_default();
                let exec_secs = ts.elapsed().as_secs_f64();
                let weight = factor.weight();
                let result = FactorResult {
                    exec_secs,
                    result: value,
                    weight,
                    details: match details {
                        Details::None => None,
                        _ => Some(details),
                    },
                };
                let mut ranking = file_object.ranking.0.blocking_lock();
                ranking.insert(factor.key().to_owned(), result);
            });
        });
    }

    fn run_io_factors(&self, selected_objects: &mut Vec<Arc<FileObject>>) {
        let handles = FuturesUnordered::new();
        for fo in selected_objects.iter() {
            for factor in self.io_factors.iter().cloned() {
                let fo = fo.clone();
                let handle = self
                    .settings
                    .runtime_async
                    .as_ref()
                    .unwrap()
                    .spawn(async move {
                        let ts = Instant::now();
                        let (value, details): (f64, Details) =
                            factor.calculate(fo.clone()).await.unwrap_or_default();
                        let exec_secs = ts.elapsed().as_secs_f64();
                        let weight = factor.weight();
                        let result = FactorResult {
                            exec_secs,
                            result: value,
                            weight,
                            details: match details {
                                Details::None => None,
                                _ => Some(details),
                            },
                        };
                        let mut ranking = fo.ranking.0.lock().await;
                        ranking.insert(factor.key().to_owned(), result);
                    });
                handles.push(handle);
            }
        }
        for handle in handles {
            self.settings
                .runtime_async
                .as_ref()
                .unwrap()
                .block_on(handle)
                .unwrap();
        }
    }

    fn run_selection_filters(&self) -> Vec<Arc<FileObject>> {
        self.file_objects
            .par_iter()
            .filter(|file_object| {
                self.selection_filters
                    .iter()
                    .all(|flt| flt.apply(file_object))
            })
            .cloned()
            .collect()
    }

    fn calculate_score(&self) {
        self.file_objects.par_iter().for_each(|fo| {
            let score = self.scoring_function.score(&fo);
            let mut juiciness = fo.juiciness.0.blocking_lock();
            *juiciness = score;
        });
    }

    pub fn run(&self) {
        let mut selected = self.run_selection_filters();

        self.run_cpu_factors(&mut selected);
        self.run_io_factors(&mut selected);
        self.calculate_score();
    }
}
