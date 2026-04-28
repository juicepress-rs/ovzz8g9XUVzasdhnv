from collections import OrderedDict
from time import time
from pathlib import Path
from typing import Any, Callable

import csv
import shutil

from ..firmware.elf_info import ELFInfo

class JuiceBox:
    def __init__(self, mode: str, fn: Callable, args: dict[str, Any]):
        self.mode: str = mode
        self._args: dict[str, Any] = args
        self._active = self._args
        self._fn = fn

    def profile(self, args) -> tuple[Path, ELFInfo, OrderedDict]:
        idx, elf = args
        if not self._active:
            result_path, elf = self._fn(elf)
            return result_path, elf, OrderedDict()
        ts_enter = time()
        result_path, elf = self._fn(elf)
        ts_exit = time()
        perfdata = OrderedDict([
            ("analysis_order_abs", idx),
            ("mode", self.mode),
            ("sha256", elf.sha),
            ("ts_enter", ts_enter),
            ("ts_exit", ts_exit),
            ("brand", elf.brand),
            ("firmware", elf.firmware),
            ("elf_path", elf.path),
            ("result_path", result_path)
        ])
        return result_path, elf, perfdata

    def writer(self) -> "JuiceBoxWriter":
        return JuiceBoxWriter(box=self, args=self._args)
    

class JuiceBoxWriter:
    _fields = [
        "analysis_order_abs",
        "mode",
        "sha256",
        "ts_enter",
        "ts_exit",
        "brand",
        "firmware",
        "elf_path",
        "result_path",
    ]

    def __init__(self, box: JuiceBox, args: dict[str, Any]):
        self.box: JuiceBox = box
        self._args = args
        self._active = self._args["profile"]
        if not self._active:
            return

        self._storage_root: Path = Path(self._args["profile_root"])
        self._storage_root.mkdir(exist_ok=True, parents=True)

        self._ts = time()

        qtype = "native"

        if self._args["queue"]:
            qtype = "juicepress"
            jp_input = self._storage_root / f"{self._ts}_{self.box.mode}_{qtype}_jpinput.json"
            shutil.copy(self._args['queue_file'], jp_input)

        self._csv_path: Path = self._storage_root / f"{self._ts}_{self.box.mode}_{qtype}_schedule.csv"
        

        self._file = open(self._csv_path, mode="w")
        self._writer = csv.DictWriter(self._file, fieldnames=self._fields)
        self._writer.writeheader()
        self._file.flush()

    def finish(self):
        if not self._active:
            return
        self._file.flush()
        self._file.close()

    def write(self, perfdata: OrderedDict):
        if not self._active:
            return
        self._writer.writerow(perfdata)
        self._file.flush()
