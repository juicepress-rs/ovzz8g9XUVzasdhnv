# alpine

Alpine's package manager `apk` does not have an easily obtainable package contents index.
There is an [online search](https://pkgs.alpinelinux.org/contents), but no resource-friendly way to dump the whole database.

So we decided to create a full `rsync` mirror of the alpine package sources. We include all versions, but only consider `x86_64` builds.
The architecture choice was arbitrary but necessary due to time and resource constraints.
Thus, if any packages contain file names with architecture-specific components, they might not be included.

1. run `00_download.bash` to rsync all `*.apk` files into `data/`
2. run `01_create_tables.py` to parse them and create the table CSVs

## About the rsync mirror

Alpine Linux provides an rsync mirror to duplicate the whole package repos.

A tutorial is available [here](https://wiki.alpinelinux.org/wiki/How_to_setup_a_Alpine_Linux_mirror).
Estimates on required disk usage (GB) in the following table:

| edge | v3.0 | v3.1 | v3.2 | v3.3 | v3.4 | v3.5 | v3.6 | v3.7 | v3.8 | v3.9 | v3.10 | v3.11 | v3.12 | v3.13 | v3.14 | v3.15 | v3.16 | v3.17 | v3.18 | v3.19 | v3.20 | v3.21 | total    |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | -------- |
| 524  | 17   | 18   | 15   | 20   | 24   | 27   | 44   | 43   | 59   | 73   | 91    | 126   | 148   | 156   | 181   | 194   | 209   | 244   | 323   | 314   | 419   | 456   | **3722** |


### rsync whitelist

We applied the following rsync filter to only grab `x86_64`:

```
--include='*/' --include='*/*/x86_64/*.apk' --exclude='*'
```

## About the APK spec

The APK spec v2 is available [here](https://wiki.alpinelinux.org/wiki/Apk_spec).

As stated, it is a tarball with several members. We parse the `.PKGINFO` file, which contains a clean package name, and then sweep over the
included file-structure to consolidate the filenames and their locations.
