#!/usr/bin/env python3

from pathlib import Path
import tarfile
import tempfile
import csv
import re


PATTERN = re.compile(r"(?:[\-_\+]\d+(?:\.\d+)*(?:[\-_\+].*)?)?\.so(?:(?:\.\d+)+)?$")


def filter_dynlib_version_extension(name) -> str:
    return PATTERN.sub(".so", name)


def main() -> None:
    dataset: dict[str, set[str]] = {}
    for i, ipk in enumerate(Path(".").glob("**/*.ipk")):
        pkg_name: str = ipk.stem.split("_")[0]
        tf: tarfile.TarFile = tarfile.open(ipk, "r")
        if pkg_name not in dataset:
            dataset[pkg_name] = set()

        for member in tf.getmembers():
            if member.name != "./data.tar.gz":
                continue
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(tf.extractfile(member).read())
                tmp.flush()
                data_gz = tarfile.open(tmp.name, "r")

                for dmem in data_gz.getmembers():
                    if not dmem.isfile():
                        continue
                    sanitized = filter_dynlib_version_extension(dmem.name[2:])
                    dataset[pkg_name].add(sanitized)
        print(i)

    print("CREATE CSV")

    packages = list(dataset.keys())
    packages.sort()

    package_f = open("openwrt_packages.csv", "wt")
    pkg_writer = csv.writer(package_f, quoting=csv.QUOTE_ALL)
    pkg_writer.writerow(["id", "name"])

    file_f = open("openwrt_files.csv", "wt")
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
