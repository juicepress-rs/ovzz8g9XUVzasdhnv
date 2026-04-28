import json
from typing import Tuple

import subprocess
import os
from mango_pipeline.juicepress.iterator import JuicePressIterator

from .juicepress import JuiceBox
from rich.console import Console
from rich.table import Table

from multiprocessing import Pool
from pathlib import Path

from .base import Pipeline, ELFInfo, MyProgress
from .firmware.elf_finder import FirmwareFinder
from .scripts import data_printer


class PipelineLocal(Pipeline):
    """
    Pipeline Process for running experiments in local docker containers
    """

    def __init__(self, *args, quiet=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiet = quiet

        self.results_dir.mkdir(parents=True, exist_ok=True)
        if self.target and self.target.is_dir():
            finder = FirmwareFinder(
                self.target,
                self.results_dir,
                bin_prep=self.bin_prep,
                exclude_libs=self.exclude_libs,
            )
            self.vendor_dict = finder.vendor_dict
        else:
            self.vendor_dict = {}

    def run_mango(self, targets: set[ELFInfo]):
        with MyProgress(
            renderable_callback=self.mango_table_wrapper, transient=True
        ) as progress:
            mango_task = progress.add_task(
                description="Mango Analysis", total=len(targets)
            )
            juice = JuiceBox(
                mode="mango", fn=self.mango_wrapper, args=self.juicepress_args
            ).writer()
            target_it = JuicePressIterator(targets, self.juicepress_args)

            with Pool(self.parallel) as p:
                args = list(zip(range(len(targets)), target_it))
                for result_path, elf, perfdata in p.imap_unordered(
                    juice.box.profile, args
                ):
                    juice.write(perfdata)
                    data_printer.parse_mango_result(
                        self.total_mango_results, result_path, elf
                    )
                    progress.update(mango_task, advance=1)
            juice.finish()

        Console().print(self.mango_table_wrapper())
        Console().print("[bold green]MANGO ANALYSIS COMPLETE")

    def mango_wrapper(self, target: ELFInfo) -> Tuple[Path, ELFInfo]:
        return self.run_analysis_container(target, "mango")

    def mango_table_wrapper(self):
        return data_printer.generate_mango_table(
            self.total_mango_results, show_dups=self.show_dups
        )

    def env_table_wrapper(self):
        return data_printer.generate_env_table(
            self.total_env_results, show_dups=self.show_dups
        )

    def run_env_resolve(self, targets: set[ELFInfo]):
        with MyProgress(
            renderable_callback=self.env_table_wrapper, transient=True
        ) as progress:
            env_task = progress.add_task(description="ENV Analysis", total=len(targets))

            juice = JuiceBox(
                mode="env", fn=self.env_wrapper, args=self.juicepress_args
            ).writer()
            target_it = JuicePressIterator(targets, self.juicepress_args)

            with Pool(self.parallel) as p:
                args = list(zip(range(len(targets)), target_it))
                for result_path, elf, perfdata in p.imap_unordered(
                    juice.box.profile, args
                ):
                    juice.write(perfdata)
                    data_printer.parse_env_result(
                        self.total_env_results, result_path, elf
                    )
                    progress.update(env_task, advance=1)

            juice.finish()

        Console().print(self.env_table_wrapper())
        self.env_merge()
        Console().print("[bold green]ENV RESOLVE COMPLETE")

    def env_wrapper(self, target: ELFInfo) -> Tuple[Path, ELFInfo]:
        return self.run_analysis_container(target, "env_resolve")

    def run_analysis_container(self, *args) -> Tuple[Path, ELFInfo]:
        target, script = args

        local_res_dir = self.result_dir_from_target(target)
        local_res_dir.mkdir(parents=True, exist_ok=True)

        if script == "mango":
            results_file = local_res_dir / f"{self.category}_results.json"
        else:
            results_file = local_res_dir / "env.json"

        if results_file.exists():
            return results_file, target

        environment = {
            "SCRIPT": script,
            "TIMEOUT": str(self.timeout),
            "RDA_TIMEOUT": str(self.rda_timeout),
            "CATEGORY": json.dumps(self.category),
            "RESULT_DEST": str(local_res_dir),  # TODO: parameterize
            "TARGET_PATH": str(target.path),  # TODO: parameterize
            "TARGET_SHA": target.sha,
            "TARGET_BRAND": target.brand,
            "TARGET_FIRMWARE": target.firmware,
            "LD_PATHS": json.dumps(target.ld_paths),
            "EXTRA_ARGS": json.dumps(["--" + x for x in self.extra_args]),
        } | os.environ.copy()

        try:
            cmd = [
                # "apptainer",
                # "run",
                # "/tmp/juicepress-mango-experiment.sif",  # TODO: parameterize
                "/entrypoint.py",
                script,
            ]
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            self.save_error_result(results_file, target, script, e.stderr)
        except Exception as e:
            self.save_error_result(results_file, target, script, str(e))

        if not results_file.exists():
            self.save_error_result(results_file, target, script, "EARLY TERMINATION")

        return results_file, target

    def print_status(self):
        targets, duplicates = self.get_experiment_targets()
        symbols = self.get_target_symbols(targets)
        self.filter_env_targets(targets, symbols)
        self.filter_mango_targets(targets, symbols)

        env_table = data_printer.generate_env_table(
            self.total_env_results, show_dups=self.show_dups
        )
        mango_table = data_printer.generate_mango_table(
            self.total_mango_results, show_dups=self.show_dups
        )

        with Console() as console:
            console.print(env_table)
            console.print(mango_table)

    def print_errors(self):
        targets, _ = self.get_experiment_targets()
        error_table = {}

        paths = []
        for target in targets:
            result_path = (
                self.results_dir
                / target.brand
                / target.firmware
                / target.sha
                / f"{self.category}_results.json"
            )
            res_data = (
                json.loads(result_path.read_text()) if result_path.exists() else {}
            )
            if (
                "ret_code" in res_data
                and res_data["ret_code"] != 0
                and res_data["ret_code"] != -9
                and res_data != 124
            ):
                mango_file = (
                    self.results_dir
                    / target.brand
                    / target.firmware
                    / target.sha
                    / f"{self.category}_mango.out"
                )
                if not mango_file.exists():
                    continue
                for line in reversed(mango_file.read_text().split("\n")):
                    line = line.strip()
                    if line:
                        if "Finished Running Analysis" in line:
                            break
                        if "angr.errors.SimMemoryMissingError" in line:
                            line = "angr.errors.SimMemoryMissingError"
                        elif any(
                            line.startswith(x)
                            for x in [
                                "INFO      |",
                                "ERROR    |",
                                "WARNING   |",
                                "WARNING  |",
                            ]
                        ):
                            paths.append(
                                (
                                    str(result_path),
                                    len(mango_file.read_text().split("\n")),
                                )
                            )
                            line = "UNKNOWN"
                        if line not in error_table:
                            error_table[line] = []
                        error_table[line].append(result_path)
                        break
        print(
            "\n".join(
                f"{x[0]} {x[1]}"
                for x in sorted(paths, reverse=True, key=lambda x: x[1])
            )
        )
        console = Console()

        table = Table(title="Mango Errors")
        table.add_column("Error")
        table.add_column("Amount")

        worst = None
        for error, count in sorted(error_table.items(), key=lambda x: len(x[1])):
            if not worst:
                worst = count
            table.add_row(error, str(len(count)))

        console.print(table)
        console.print(worst)
