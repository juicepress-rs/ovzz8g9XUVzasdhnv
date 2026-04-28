#!/usr/bin/env python3

from pathlib import Path
import tarfile
import tempfile
import subprocess
import csv
import re


PATTERN = re.compile(r"(?:[\-_\+]\d+(?:\.\d+)*(?:[\-_\+].*)?)?\.so(?:(?:\.\d+)+)?$")


def filter_dynlib_version_extension(name) -> str:
    return PATTERN.sub(".so", name)


def main() -> None:
    dataset: dict[str, set[str]] = {}

    for i, ipk in enumerate(Path("oe-walnascar/build/tmp/work").glob("**/*.ipk")):
        pkg_name: str = ipk.stem.split("_")[0]

        if pkg_name not in dataset:
            dataset[pkg_name] = set()

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["ar", "x", str(ipk.absolute())], cwd=tmpdir, check=True)
            data_zst = Path(tmpdir) / "data.tar.zst"
            assert data_zst.exists()
            subprocess.run(["zstd", "-d", str(data_zst)], cwd=tmpdir, check=True)
            data_tar = Path(tmpdir) / "data.tar"
            data = tarfile.open(data_tar, "r")
            for dmem in data.getmembers():
                if not dmem.isfile():
                    continue
                sanitized = filter_dynlib_version_extension(dmem.name[2:])
                dataset[pkg_name].add(sanitized)
        print(i)

    print("CREATE CSV")

    packages = list(dataset.keys())
    packages.sort()

    package_f = open("openembedded_pkg.csv", "wt")
    pkg_writer = csv.writer(package_f, quoting=csv.QUOTE_ALL)
    pkg_writer.writerow(["id", "name"])

    file_f = open("openembedded_file.csv", "wt")
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
