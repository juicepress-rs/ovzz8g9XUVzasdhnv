#!/usr/bin/env python

from pathlib import Path
import json
import hashlib


def main():
    folder = Path("./reports/")
    for i, json_file in enumerate(folder.glob("*juicepress*.json")):
        print(i)
        if "masked" in json_file.stem:
            continue
        components = json_file.stem.split("___")
        components[2] = hashlib.sha256(components[2].encode()).hexdigest()
        output_file = folder / f"{Path('___'.join(components)).stem}-masked.json"
        print(output_file)

        data = json.loads(json_file.read_text())

        for result in data["results"]:
            result["sha256"] = hashlib.sha256(result["sha256"].encode()).hexdigest()
            for k in result["ranking_by_factor"].keys():
                del result["ranking_by_factor"][k]["details"]
                del result["ranking_by_factor"][k]["weight"]

            del result["name"]
            del result["path"]
            result["root_relative_path"] = hashlib.sha256(
                result["root_relative_path"].encode()
            ).hexdigest()

        output_file.write_text(json.dumps(data))
        json_file.unlink()


if __name__ == "__main__":
    main()
