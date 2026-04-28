# fw-fs-downloader

Uses a list of UIDs as input and outputs the included file systems as archives.

## Installation

Either use the venv from FACT('s backend) or run `poetry install` from the project's folder.

## Usage

Either run from FACT's src directory (backend)...

```shell
python3 find_filesystems.py \
  35d8bd8fd8a3dfb0bb6752104d0f76d1908e5f68c210ef7eff20e08dc70a943f_54287958 [more UIDs...]
```

... or provide the path of the directory as parameter and run it with poetry:

```shell
poetry run fw_fs_downloader \
  --fact-src-dir /home/user/git/FACT_core/src \
  35d8bd8fd8a3dfb0bb6752104d0f76d1908e5f68c210ef7eff20e08dc70a943f_54287958 [more UIDs...]
```

The script also accepts JSON files with an array of firmware UIDs as input:

```shell
echo '["35d8bd8fd8a3dfb0bb6752104d0f76d1908e5f68c210ef7eff20e08dc70a943f_54287958"]' > foo.json
poetry run fw_fs_downloader --fact-src-dir /home/user/git/FACT_core/src foo.json
```

See also `python3 find_filesystems.py --help`.
