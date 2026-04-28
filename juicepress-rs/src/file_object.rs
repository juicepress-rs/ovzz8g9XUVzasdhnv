use elf::ElfBytes;
use elf::endian::AnyEndian;
use hex;
use jwalk::{DirEntry, WalkDir};
use lazy_regex::regex_replace;
use rayon::iter::{ParallelBridge, ParallelIterator};
use serde::{Serialize, Serializer};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;
use tree_magic_mini;

use super::factor::FactorResult;

pub struct MutexWrapper<T: ?Sized>(pub Mutex<T>);
impl<T: ?Sized + Serialize> Serialize for MutexWrapper<T> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        self.0.blocking_lock().serialize(serializer)
    }
}

#[derive(Serialize)]
pub struct FileObject {
    #[serde(skip_serializing)]
    pub finfo: DirEntry<((), ())>,
    pub path: String,
    pub name: String,
    #[serde(skip_serializing)]
    pub mime: String,
    pub sha256: String,
    pub size: usize,
    #[serde(skip_serializing)]
    pub bytes: Vec<u8>,
    pub root_relative_path: PathBuf,
    #[serde(skip_serializing)]
    pub sanitized_filename: String,
    pub juiciness: MutexWrapper<f64>,
    #[serde(rename = "ranking_by_factor")]
    pub ranking: MutexWrapper<HashMap<String, FactorResult>>,
    #[serde(skip_serializing)]
    pub userspace_elf: bool,
}

pub trait FileNameExt {
    fn filenames(&self) -> HashSet<String>;
}

impl FileNameExt for Vec<Arc<FileObject>> {
    fn filenames(&self) -> HashSet<String> {
        self.iter()
            .map(|fo| fo.sanitized_filename.to_owned())
            .collect()
    }
}

impl FileObject {
    fn create_with_arc(finfo: DirEntry<((), ())>, root_dir: &String) -> Option<Arc<Self>> {
        let bytes = fs::read(finfo.path());

        if bytes.is_err() {
            eprintln!("error reading file {:?}", finfo.path());
            return None;
        }

        let bytes = bytes.unwrap();

        let root_relative_path = finfo
            .path()
            .strip_prefix(root_dir)
            .expect("could not strip root dir prefix")
            .to_owned();

        let slice = bytes.as_slice();
        let mime = tree_magic_mini::from_u8(slice).to_string();
        let sha256 = hex::encode(Sha256::digest(slice));

        // removes version strings from library filenames, e.g.:
        // libsome-1.0.0.so
        // libsome1.so
        // libsome-1.0.0-git.so
        // libsome.so.20251010
        // libsome.so.1.0.0
        // ==> libsome.so
        let sanitized_filename = regex_replace!(
            r"(?:[\-_\+]\d+(?:\.\d+)*(?:[\-_\+].*)?)?\.so(?:(?:\.\d+)+)?$",
            finfo.file_name().to_str().unwrap(),
            ".so"
        )
        .into_owned();

        let mut fo = FileObject {
            name: finfo.file_name().to_string_lossy().into(),
            path: finfo.path().to_string_lossy().into(),
            finfo,
            mime,
            sha256,
            size: bytes.len(),
            bytes,
            root_relative_path,
            sanitized_filename,
            ranking: MutexWrapper(Mutex::new(std::collections::HashMap::new())),
            juiciness: MutexWrapper(Mutex::new(0.0)),
            userspace_elf: false,
        };
        fo.userspace_elf = fo.is_userspace_elf();
        Some(fo.into())
    }

    pub fn collect(root_dir: &String) -> Vec<Arc<FileObject>> {
        WalkDir::new(root_dir)
            .skip_hidden(false)
            .follow_links(false)
            .into_iter()
            .par_bridge()
            .flatten()
            .filter(|finfo| {
                // exclude virtual file systems
                !finfo.path().starts_with("/proc")
                    && !finfo.path().starts_with("/dev")
                    && !finfo.path().starts_with("/sys")
                    && finfo.path().is_file()
            })
            .filter_map(|finfo| Self::create_with_arc(finfo, &root_dir))
            .collect()
    }

    pub fn parse_elf(&self) -> Option<ElfBytes<'_, AnyEndian>> {
        if !self.userspace_elf {
            return None;
        }
        let elf = ElfBytes::<AnyEndian>::minimal_parse(&self.bytes.as_slice());
        elf.ok()
    }

    fn is_userspace_elf(&self) -> bool {
        let no_symlink = !self.finfo.file_type().is_symlink();
        let no_kernel_module = !self.finfo.file_name().to_string_lossy().ends_with(".ko");
        let no_obj = !self.finfo.file_name().to_string_lossy().ends_with(".o");
        let elf_mime = [
            "application/x-executable",
            "application/x-pie-executable",
            "application/x-sharedlib",
        ]
        .contains(&self.mime.as_str());

        no_kernel_module && elf_mime && no_symlink & no_obj
    }
}
