#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import tarfile
from pathlib import Path

from rich.progress import Progress

from .utils import setup_logging, CONSOLE

try:
    from config import load
    from storage.fsorganizer import FSOrganizer
except (ImportError, ModuleNotFoundError):
    load, FSOrganizer = None, None

logger = setup_logging()
fso = FSOrganizer() if FSOrganizer is not None else None


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--paths",
        "-p",
        default=[],
        type=lambda a: a.split(","),
        help="comma-separated list of root paths to use as FS indicators",
    )
    parser.add_argument(
        "--min-file-count",
        "-c",
        type=int,
        default=1,
        help="minimum number of paths that begin with a root path to count this file as FS",
    )
    parser.add_argument(
        "--path-threshold",
        "-t",
        type=int,
        default=1,
        help="minimum number of paths that fulfill the min file count requirement",
    )
    parser.add_argument(
        "firmware",
        help="either UIDs of firmware images or JSON files containing an array with UIDs",
        nargs="+",
    )
    parser.add_argument(
        "-output-directory",
        "-o",
        help="the output directory to store the results (default: ./output)",
        type=Path,
        default=Path.cwd() / "output",
    )
    parser.add_argument(
        "--compress",
        "-x",
        action="store_true",
    )
    parser.add_argument(
        "--no-download",
        "--json",
        "-j",
        action="store_true",
        help="do not download files, instead output only the metadata as JSON.",
    )
    parser.add_argument(
        "--fact-src-dir",
        "-d",
        help="the src directory of FACT's backend (by default the script assumes that it is located in the src dir)",
        type=Path,
    )
    return parser.parse_args()


def save_as_archive(db, output_path: Path, uid_list: list[str], parent_uid: str, compress: bool):
    vfp_list = db.get_vfps_for_uid_list(uid_list)

    with tarfile.open(output_path, "w:gz" if compress else "w") as tar:
        count = 0
        for uid in uid_list:
            # the file can exist multiple times in the FS, but all are included in the VFP path list
            source_path = fso.generate_path_from_uid(uid)
            try:
                for archive_path in vfp_list[uid][parent_uid]:
                    tar.add(source_path, arcname=archive_path)
                    count += 1
            except KeyError:
                logger.error(f'File with UID "{uid}" not found in database.')
        logger.info(f'Saved filesystem with UID "{uid}" to {output_path.name} ({count} files)')


def _load_fw_uids(fw_input_args: list[str]) -> list[str]:
    fw_uids = set()
    for element in fw_input_args:
        # the elements should be either a UID or a path to a JSON file that contains an array with UIDs
        path = Path(element)
        if not path.is_file():
            fw_uids.add(element)
            continue
        try:
            uid_list = json.loads(path.read_text())
            assert isinstance(uid_list, list)
            fw_uids.update(
                {str(e) for e in uid_list}
            )  # make sure everything is a str to prevent errors
            logger.info(f"Loaded {len(fw_uids)} FW UIDs from {path.name}")
        except json.JSONDecodeError:
            logger.error(f"File {path.name} is not a valid JSON file")
        except (AssertionError, ValueError):
            logger.error(f"File {path.name} does not contain a valid array of UIDs")
        except Exception as error:
            logger.exception(
                f"Unexpected exception when trying to load UIDs from JSON file {path.name}: {error}"
            )
    return sorted(fw_uids)


def find_filesystems(fw_uids: list[str], args):
    # delayed import to make sure the "import hack" is active if needed
    from .db_interface import CustomDbInterface

    db = CustomDbInterface()

    json_result = {}
    with Progress(console=CONSOLE) as progress:
        task1 = progress.add_task("[red]processing FW samples...", total=len(fw_uids))
        for root_uid in fw_uids:
            if not db.is_firmware(root_uid):
                logger.error(f'Firmware with UID "{root_uid}" not found in database.')
                continue

            filesystems = db.find_filesystems(
                root_uid,
                file_count=args.min_file_count,
                path_count=args.path_threshold,
                root_paths=args.paths,
            )
            if not filesystems:
                continue
            sha256 = root_uid.split("_")[0]
            task2 = progress.add_task(
                f"[green]Processing filesystems in {root_uid}...",
                total=len(filesystems),
            )
            for index, uid in enumerate(filesystems):
                logger.info(f"Found filesystem with UID '{uid}' in file with UID '{root_uid}'")
                fs_fo = db.get_object(uid)

                if args.no_download:
                    json_result.setdefault(sha256, []).append(uid)
                else:
                    output_path = (
                        args.output_directory
                        / f"{sha256}_fs_{index}.{'tar.gz' if args.compress else 'tar'}"
                    )
                    if output_path.is_file():
                        logger.warning(
                            f'Skipping file with UID "{uid}": already exists in output directory.'
                        )
                    else:
                        save_as_archive(db, output_path, fs_fo.files_included, uid, args.compress)
                progress.advance(task2)
            progress.advance(task1)

    if args.no_download:
        print(json.dumps(json_result, indent=2))


def main():
    global load, fso
    args = _parse_args()

    if load is None:
        # *import hack*: if the import failed previously we add args.fact_src_dir to sys.path and try again
        if not args.fact_src_dir:
            logger.error(
                "The script must either be run from FACT's backend src dir or --fact-src-dir must be specified"
            )
            sys.exit(1)
        elif not Path(args.fact_src_dir).is_dir():
            logger.error(f"The src dir {args.fact_src_dir} is not a directory")
            sys.exit(2)
        sys.path.append(str(Path(args.fact_src_dir).resolve().absolute()))
        from config import load
        from storage.fsorganizer import FSOrganizer

    load()
    fso = fso or FSOrganizer()

    args.output_directory.mkdir(parents=True, exist_ok=True)
    fw_uids = _load_fw_uids(args.firmware)

    find_filesystems(fw_uids, args)


if __name__ == "__main__":
    main()
