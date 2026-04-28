#!/usr/bin/env python3

from pathlib import Path
import tarfile
import csv
import re
from typing import IO

PATTERN = re.compile(r"(?:[\-_\+]\d+(?:\.\d+)*(?:[\-_\+].*)?)?\.so(?:(?:\.\d+)+)?$")

def filter_dynlib_version_extension(name) -> str:
    return PATTERN.sub(".so", name)

def main() -> None:
    dataset: dict[str, set[str]] = {}
    pkg_pattern: re.Pattern = re.compile(r"^pkgname\s*=\s*(.+)", re.MULTILINE)
    for i, apk in enumerate(Path(".").glob("data/**/*.apk")):
        tf: tarfile.TarFile = tarfile.open(apk, "r")

        b_pkginfo_stream: IO[bytes] | None = tf.extractfile(tf.getmember(".PKGINFO"))
        assert b_pkginfo_stream is not None

        pkginfo: str = b_pkginfo_stream.read().decode()

        mg: re.Match | None = pkg_pattern.search(pkginfo)
        assert mg is not None

        pkg_name: str = mg.group(1)
        if pkg_name not in dataset:
            dataset[pkg_name] = set()

        for member in tf.getmembers():
            if ".PKGINFO" in member.name or ".SIGN.RSA.alpine" in member.name:
                # skip special files
                continue
            if not member.isfile():
                continue
            sanitized = filter_dynlib_version_extension(member.name)
            dataset[pkg_name].add(sanitized)
        print(i)

    print("CREATE CSV")

    packages: list[str] = list(dataset.keys())
    packages.sort()

    package_f = open("alpine_pkg.csv", "wt")
    pkg_writer = csv.writer(package_f, quoting=csv.QUOTE_ALL)
    pkg_writer.writerow(["id", "name"])

    file_f = open("alpine_file.csv", "wt")
    file_writer = csv.writer(file_f, quoting=csv.QUOTE_ALL)
    file_writer.writerow(["id", "file_name", "location", "package_id"])

    file_id = 0

    for pkg_id, pkg in enumerate(packages):
        print(pkg)
        pkg_writer.writerow([pkg_id, pkg])
        for filename_dirty in sorted(dataset[pkg]):
            file_name = Path(filename_dirty).name
            location = str(Path(filename_dirty).parent)
            file_writer.writerow([file_id, file_name, location, pkg_id])
            file_id += 1

    file_f.close()
    package_f.close()


if __name__ == "__main__":
    main()
