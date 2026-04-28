#!/usr/bin/env python3

from pathlib import Path
import json
import csv
import re


PATTERN = re.compile(r"(?:[\-_\+]\d+(?:\.\d+)*(?:[\-_\+].*)?)?\.so(?:(?:\.\d+)+)?$")


def filter_dynlib_version_extension(name) -> str:
    return PATTERN.sub(".so", name)


def clean_deps(info) -> set:
    dep_files = set()
    for dep in info["dependencies"]:
        if dep.startswith("host-"):
            continue
        prefix = f"buildroot-2025.02.2/output/per-package/{dep}/target/"
        dep_files |= {str(p).replace(prefix, "") for p in Path(prefix).glob("**/*")}
    return dep_files


def initial_tree(name) -> set:
    pkg_tree = set()
    prefix = f"buildroot-2025.02.2/output/per-package/{name}/target/"
    for p in Path(prefix).glob("**/*"):
        if not p.is_file():
            continue
        pkg_tree |= {str(p).replace(prefix, "")}
    return pkg_tree


def main():
    pkg_info = json.loads(Path("buildroot-2025.02.2/package_info.json").read_bytes())
    result = {}
    for name, info in pkg_info.items():
        if name.startswith("host-"):
            continue
        pkg_tree = initial_tree(name) - clean_deps(info)
        result[name] = list(pkg_tree)

    packages = list(result.keys())
    packages.sort()

    package_f = open("buildroot_packages.csv", "wt")
    pkg_writer = csv.writer(package_f, quoting=csv.QUOTE_ALL)
    pkg_writer.writerow(["id", "name"])

    file_f = open("buildroot_files.csv", "wt")
    file_writer = csv.writer(file_f, quoting=csv.QUOTE_ALL)
    file_writer.writerow(["id", "file_name", "location", "package_id"])

    file_id = 0

    for pkg_id, pkg in enumerate(packages):
        print(pkg)
        pkg_writer.writerow([pkg_id, pkg])
        for filename_dirty in sorted(result[pkg]):
            file_name = filter_dynlib_version_extension(Path(filename_dirty).name)
            location = str(Path(filename_dirty).parent)
            file_writer.writerow([file_id, file_name, location, pkg_id])
            file_id += 1

    file_f.close()
    package_f.close()


if __name__ == "__main__":
    main()
