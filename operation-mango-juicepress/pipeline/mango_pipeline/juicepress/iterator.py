from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json
from collections import deque

from mango_pipeline.firmware.elf_info import ELFInfo



class JuicePressIterator:
    @dataclass(order=True)
    class _Item:
        juiciness: float
        elf: ELFInfo = field(compare=False)
        jp_data: dict[str, Any] = field(compare=False)

    def __init__(self, elf_files: set[ELFInfo], args: dict[str, Any]) -> None:
        self._args: dict[str, Any] = args
        self._elf_files: set[ELFInfo] = elf_files
        
        if self._args["queue"]:
            self._prio_data: list[dict[str, Any]] = self._load_juicepress_file()
            self._prio_idx: dict[str, dict[str, Any]] = self._create_idx()

        self._pq: deque[JuicePressIterator._Item] = self._build_queue()

    def _load_juicepress_file(self) -> list[dict[str, Any]]:
        return json.loads(self._args["queue_file"].read_bytes().decode())["results"]

    def _create_idx(self) -> dict[str, dict[str, Any]]:
        return {
            f"{pr['name']}_{pr['sha256']}": pr for pr in self._prio_data # pyright: ignore
        }

    def _build_queue(self) -> deque["JuicePressIterator._Item"]:
        raw: list[JuicePressIterator._Item] = []

        if not self._args["queue"]:
            # juicepress deactivated, default mango behavior
            raw += [JuicePressIterator._Item(juiciness=0.0, elf=elf, jp_data={}) for elf in self._elf_files]
            return deque(raw)

        for elf in self._elf_files:
            name = Path(elf.path).name
            index_key = f"{name}_{elf.sha}"
            assert index_key in self._prio_idx

            prio = self._prio_idx[index_key]

            raw.append(
                JuicePressIterator._Item(juiciness=prio["juiciness"], elf=elf, jp_data=prio)
            )
    
        # descending juiciness, use sha256 as secondary key to ensure order when two elfs have the same
        # juiciness but are appended to the list in pseudoranom order (set[ELFInfo] yields items based on mem-loc)
        # sum of all chrs in the name is the third key, just to be sure.
        ordered = sorted(raw, reverse=True, key=lambda x: (x.juiciness, int(x.elf.sha, 16), sum(ord(char) for char in x.jp_data["name"])))
        return deque(ordered)

    def __iter__(self):
        return self

    def __next__(self):
        if len(self._pq) == 0:
            raise StopIteration
        return self._pq.popleft().elf

