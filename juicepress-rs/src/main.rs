mod factor;
mod file_object;
mod report;
mod scheduler;
mod scoring;
mod selection;
mod settings;

use std::time::Instant;

pub use file_object::{FileNameExt, FileObject};
pub use report::Report;
pub use scheduler::Scheduler;
pub use settings::Settings;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let settings = Settings::new()?;

    // collect files
    let mut before = Instant::now();
    let file_objects = FileObject::collect(&settings.path);
    let collection_sec = before.elapsed().as_secs_f64();

    let sched = Scheduler::new(&settings, &file_objects);

    before = Instant::now();
    sched.run();
    let analysis_sec = before.elapsed().as_secs_f64();

    let report = Report::new(analysis_sec, collection_sec, &settings.path, file_objects);
    report.save(&settings.output);

    Ok(())
}
