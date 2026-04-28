from __future__ import annotations

from storage.db_interface_backend import BackendDbInterface
from storage.schema import AnalysisEntry, FirmwareEntry, VirtualFilePath, fw_files_table

from sqlalchemy import func, select

ROOT_PATHS = ('bin', 'var', 'www', 'etc', 'sbin', 'boot', 'home', 'lib', 'opt', 'root', 'srv', 'usr')
ARCH_KEY_DICT = {
    'arc': ['arcompact', 'arcv2', 'arcv3'],
    'arm': ['arm', 'aarch64'],
    'hexagon': ['qdsp'],
    'motorola': ['m68k', 'm88k', 'coldfire', 'm68hc', 'mc68hc', 'motorola'],
    'mips': ['mips'],
    'ppc': ['ppc', 'powerpc'],
    'riscv': ['riscv', 'risc-v'],
    'sparc': ['sparc'],
    's390': ['s/390'],
    'x86': ['x86', '80386', 'amd64', 'i386', 'i486'],
    'xtensa': ['xtensa'],
}


class CustomDbInterface(BackendDbInterface):
    def find_filesystems(
        self,
        root_uid: str,
        root_paths: list[str] | None = None,
        file_count: int = 1,
        path_count: int = 1,
    ) -> list[str]:
        if not root_paths:
            root_paths = ROOT_PATHS
        assert path_count <= len(root_paths), 'the path count must be at least as big as the minimum number of paths'
        # otherwise the result would be always emtpy

        candidates = {}
        for root_path in root_paths:
            with self.get_read_only_session() as session:
                query = (
                    select(
                        VirtualFilePath.parent_uid,
                        # count of the paths that begin with a specific root folder
                        func.count().filter(VirtualFilePath.file_path.like(f'/{root_path}/%')),
                    )
                    # join with the fw_files_table to make sure the FS is in the FW with root_uid
                    .join(fw_files_table, VirtualFilePath.parent_uid == fw_files_table.c.file_uid)
                    .filter(fw_files_table.c.root_uid == root_uid)
                    .group_by(VirtualFilePath.parent_uid)
                )
                for parent, count in session.execute(query):
                    if count < file_count:
                        continue
                    candidates.setdefault(parent, 0)
                    candidates[parent] += 1
        return [candidate for candidate, count in candidates.items() if count >= path_count]

    def get_fw_uids_by_md5_list(self, md5_list: list[str]) -> dict[str, str]:
        with self.get_read_only_session() as session:
            query = (
                select(AnalysisEntry.result.op('->>')('md5'), FirmwareEntry.uid)
                .join(AnalysisEntry, AnalysisEntry.uid == FirmwareEntry.uid)
                .filter(AnalysisEntry.result.op('->>')('md5').in_(md5_list))
            )
            return {md5: uid for md5, uid in session.execute(query)}  # noqa: C416

    def count_all_files_in_fw(self, fw_uid: str) -> int:
        with self.get_read_only_session() as session:
            query = select(func.count(fw_files_table.c.file_uid)).where(fw_files_table.c.root_uid == fw_uid)
            return session.execute(query).scalar()

    def find_elf_architectures(self, fw_uid: str) -> list[str]:
        with self.get_read_only_session() as session:
            query = (
                select(AnalysisEntry.result.op('->>')('full'))
                .join(fw_files_table, AnalysisEntry.uid == fw_files_table.c.file_uid)
                .filter(fw_files_table.c.root_uid == fw_uid)
                .filter(AnalysisEntry.plugin == 'file_type')
                .filter(AnalysisEntry.result.op('->>')('full').like('ELF %'))
            )
            architectures = set()
            for type_str in session.execute(query.distinct()).scalars():
                arch = type_str.split(',', maxsplit=3)[1].strip().lower()
                architectures.add(arch)
            filtered_architectures = set()
            for arch, keys in ARCH_KEY_DICT.items():
                if any(key in elf_arch for elf_arch in architectures for key in keys):
                    filtered_architectures.add(arch)
            return sorted(filtered_architectures)

    def find_linux_kernels(self, fw_uid: str) -> list[str]:
        with self.get_read_only_session() as session:
            subquery = (
                select(func.unnest(AnalysisEntry.summary).label('item'))
                .join(fw_files_table, AnalysisEntry.uid == fw_files_table.c.file_uid)
                .filter(fw_files_table.c.root_uid == fw_uid)
                .filter(AnalysisEntry.plugin == 'software_components')
                .subquery()
            )
            query = select(subquery.c.item).filter(subquery.c.item.ilike('linux kernel%'))
            return sorted(set(session.execute(query).scalars()))