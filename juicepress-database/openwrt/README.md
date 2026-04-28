# openwrt

OpenWrt's package manager `opkg` uses `ipk` files. An overview of the manager and format can be found in this [slide deck by Alejandro del Castillo](https://elinux.org/images/2/24/Opkg_debians_little_cousin.pdf) There is no easily obtainable package contents index.

So we decided to create a full `rsync` mirror of the package sources. We include all versions, but only consider `x86_64` builds.
The architecture choice was arbitrary but necessary due to time and resource constraints.
Thus, if any packages contain file names with architecture-specific components, they might not be included.

1. run `00_download.bash` to rsync all `*.ipk` files into `data/`
2. run `01_create_tables.py` to parse them and create the table CSVs

## About the rsync mirror

OpenWrt provides an rsync mirror to duplicate the whole package repos.

A tutorial is available [here](https://openwrt.org/docs/guide-user/additional-software/opkg#local_repository).


### rsync whitelist

We applied the following rsync filter to only grab `x86_64`:

```
--include='*/' --include='*/x86*/**/*.ipk' --exclude='*' --exclude='snapshots/'
```

## About the IPK format

An `ipk` is very similar to the [Debian package format](https://man7.org/linux/man-pages/man5/deb.5.html).
It is a `gzip`-compressed tar with two relevant segments: `control.tar.gz` and `data.tar.gz`.
The latter contains the UNIX file structure to be installed into the file system. `control` contains meta data.
The `ipk` naming convention is rather clean, which is why we can extract the package name from the `ipk` itself·

We sweep over the `data.tar.gz` to collect all filenames and locations.
