#!/usr/bin/env python3

from pathlib import Path
import re
import csv

PATTERN = re.compile(r"(?:[\-_\+]\d+(?:\.\d+)*(?:[\-_\+].*)?)?\.so(?:(?:\.\d+)+)?$")

def filter_dynlib_version_extension(name) -> str:
    return PATTERN.sub(".so", name)


def main() -> None:
    pattern: re.Pattern = re.compile(r"^(.+)\s+(.+)$")
    dataset: dict[str, set[str]] = {}
    for p_contents in Path("data").glob("**/trusty/Contents-ppc64el"):
        print(f"Parse {p_contents}")
        with p_contents.open("r", encoding="latin1") as f:
            cnt: int = 0
            skip: bool = False
            for line in f:
                cnt += 1
                # older Contents had an inconvenient header full of text, skip it.
                if line.startswith("This"):
                    skip = True
                if line.startswith("FILE"):
                    # reached pkg list
                    skip = False
                    continue
                if skip:
                    continue
                matches: re.Match | None = pattern.search(line)
                if matches is None:
                    continue
                filepath: str = matches.group(1)
                packages: list[str] = matches.group(2).split(",")

                for pkg in packages:
                    if pkg not in dataset:
                        dataset[pkg] = set()
                    dataset[pkg].add(filepath)
            print(f"Parsed {cnt} lines")
    print("CREATE CSV")

    packages = list(dataset.keys())
    packages.sort()

    package_f = open("ubuntu_pkg.csv", "wt")
    pkg_writer = csv.writer(package_f, quoting=csv.QUOTE_ALL)
    pkg_writer.writerow(["id", "name"])

    file_f = open("ubuntu_file.csv", "wt")
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
