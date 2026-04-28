use super::stringsearch_devel::*;

use elf::ElfBytes;
use elf::endian::AnyEndian;
use elf::symbol::Symbol;
use serde::Deserialize;

// from: https://github.com/sefcom/operation-mango-public/blob/master/package/argument_resolver/external_function/input_functions.py
// some symbols are omnipresent, which is why I deactivated them.
static TAINT_SYMBOL_NAMES: &'static [&str] = &[
    //"read",
    //"fread",
    //"fgets",
    //"recv",
    //"recvfrom",
    "custom_param_parser",
    "system",
    "twsystem",
    "execFormatCmd",
    "exec_cmd",
    "___system",
    "bstar_system",
    "doSystemCmd",
    "doShell",
    "CsteSystem",
    "cgi_deal_popen",
    "ExeCmd",
    "ExecShell",
    "exec_shell_popen",
    "exec_shell_popen_str",
    "popen",
    "execl",
    "execlp",
    "execle",
    "execv",
    "execvp",
    "execvpe",
    "execve",
    "tp_systemEx",
    "exec_shell_async",
    "exec_shell_sync",
    "exec_shell_sync2",
    "SLIBCSystem",
    "SLIBCExecl",
    "SLIBCExec",
    "SLIBCExecv",
    "SLIBCPopen",
    "pegaSystem",
    //"popen",
    //"fopen",
    //"strcat",iter
    //"strcpy",
    //"memcpy",
    //"gets",
    //"sprintf",
    //"snprintf",
    "getenv",
    "GetValue",
    "acosNvramConfig_get",
    "acosNvramConfig_read",
    "nvram_get",
    "nvram_safe_get",
    "bcm_nvram_get",
    "envram_get",
    "wlcsm_nvram_get",
    "dni_nvram_get",
    "PTI_nvram_get",
    "setenv",
    "SetValue",
    "httpSetEnv",
    "acosNvramConfig_set",
    "acosNvramConfig_write",
    "nvram_set",
    "nvram_safe_set",
    "bcm_nvram_set",
    "envram_set",
    "wlcsm_nvram_set",
    "dni_nvram_set",
    "PTI_nvram_set",
];

enum StringTableKind {
    DynSym,
    SymTab,
}

#[derive(Serialize)]
pub struct TaintSymbolResultDetails {
    pub found: Vec<String>,
}

#[derive(Clone, Deserialize, Default)]
pub struct TaintSymbol {
    interesting: HashSet<String>,
}

impl TaintSymbol {
    fn extract_symbol_names_from(
        &self,
        elf: &ElfBytes<AnyEndian>,
        what: StringTableKind,
    ) -> Option<HashSet<String>> {
        let (sym, tab) = match what {
            StringTableKind::DynSym => elf.dynamic_symbol_table().ok()??,
            StringTableKind::SymTab => elf.symbol_table().ok()??,
        };
        let names: HashSet<String> = sym
            .into_iter()
            .map(|sym| tab.get(sym.st_name as usize).unwrap_or_default().to_owned())
            .filter(|x| x != "")
            .collect();
        Some(names)
    }
}

impl CPUFactor for TaintSymbol {
    fn calculate(&self, file_object: &FileObject) -> Option<(f64, Details)> {
        let elf = file_object.parse_elf()?;

        let dynsym = self
            .extract_symbol_names_from(&elf, StringTableKind::DynSym)
            .unwrap_or_default();
        let sym = self
            .extract_symbol_names_from(&elf, StringTableKind::SymTab)
            .unwrap_or_default();

        let combined: HashSet<String> = dynsym.union(&sym).map(|union| union.to_owned()).collect();

        let intersection: Vec<String> = combined.intersection(&self.interesting).cloned().collect();

        if intersection.len() > 0 {
            Some((
                1.0,
                Details::TaintSymbol(TaintSymbolResultDetails {
                    found: intersection,
                }),
            ))
        } else {
            None
        }
    }

    fn weight(&self) -> f64 {
        1.0
    }

    fn key(&self) -> String {
        "known_taint_symbol".to_owned()
    }
}

impl TaintSymbol {
    #[allow(unused_variables)]
    pub fn new(settings: Settings) -> Self {
        let interesting: HashSet<String> = TAINT_SYMBOL_NAMES
            .into_iter()
            .map(|s| String::from(s.to_owned()))
            .collect();
        Self { interesting }
    }
}
