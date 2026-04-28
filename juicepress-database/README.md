# juicepress-database

JuicePress provides a variety of io-based scoring factors that require a database backend.

This repository provides a Dockerfile to create the database backend.
The subfolders provide more information on each source to help you replicate and understand how we built the database for package guesses.

## Build and Run

In this folder, execute:

```sh
docker compose up -d
```

A postgresql-database with read-only user `juicepress:juicepress` will run on `127.0.0.1:2345`.

## Source Overview

Sources are queried by a [PostgreSQL](https://www.postgresql.org/) database to guess the origin of a file by searching for package contents overlaps in the firmware image.


| **source**     | **collection date** | **collection method** | **db table prefix**  | **url**                                                                                                                  | **packages**    | **files**    | **files per package (mean)** | **csv seed sizes pkg / file (bytes) ** | **limitations**                                                                                                                                                     | **notes**                                                                                                                                                                                                                                          |
|----------------|---------------------|-----------------------|----------------------|--------------------------------------------------------------------------------------------------------------------------|-----------------|--------------|------------------------------|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `alpine`       | `2025-10-01`        | package repo mirror   | `alpine_`            | `https://wiki.alpinelinux.org/wiki/How_to_setup_a_Alpine_Linux_mirror`                                                   | `40,596`        | `8,096,572`  | `199.4426`                   | `1,061,580` / `741,960,133`            | `x86_64`                                                                                                                                                            | mirrored official repos across all versions, extracted package and path info from `apk` format, deduplicated all packages across versions, joined the filepaths                                                                                    |
| `buildroot`    | `2025-05-19`        | allyesconfig build    | `buildroot_`         | `https://gitlab.com/buildroot.org/buildroot/`                                                                            | `2,043`         | `149,093`    | `72.9775`                    | `43,160` / `10,271,427`                | `x86_64`, uncompilable packages disabled                                                                                                                            | `v2025.02.2`, enabled all packages, built, iteratively disabled all broken packages until build successfully finished, then traversed per-package output folders to collect info                                                                   |
| `manpage`      | `2025-04-28`        | package repo index    | `ubuntu_`            | `http://archive.ubuntu.com/ubuntu/dists/`                                                                                | `N/A`           | `228,314`    | `N/A`                        | `-` / `-`                              | manpages available in ubuntu                                                                                                                                        | virtual source, special query on the ubuntu package info that searches for case-insensitive hits in the `usr/share/man/%` location. ubuntu because most packages and, thus, most complete pages                                                    |
| `nsrl`         | `2025-04-23`        | download              | `nsrl_`              | `https://www.nist.gov/itl/ssd/software-quality-group/national-software-reference-library-nsrl/nsrl-download/current-rds` | `N/A`           | `13,393,802` | `N/A`                        | `-` / `494,616,319`                    | only files associated with UNIX operating systems, inherently dirty dataset, no package guestimates possible                                                        | `v2025.03.1-modern,-legacy` NSRL RDS hash sets, merged, deduplicated, removed all packages not associated with unixoid operating system sources, minified (no hashs, only filenames)                                                               | 
| `openembedded` | `2025-10-04`        | allyesconfig build    | `openembedded_`      | `https://git.openembedded.org/`                                                                                          | `12,117`        | `385,153`    | `31.7862`                    | `389,496` / `32,560,311`               | `x86_64`, uncompilable packages disabled, layers: `meta-openembedded/* (excl gnome and xfce)`, `meta-clang/*`, `meta-poky/*`, `meta-yocto-bsp/*`, `meta-skeleton/*` | `walnascar`, enabled all packages from openembedded layers (including official core layers and -contrib, minus xfce and gnome), built, iteratively disabled all broken packages until build successfully finished, enabled per-package `ipk` output and parsed them |
| `openwrt`      | `2025-05-07`        | package repo mirror   | `openwrt_`           | `https://openwrt.org/downloads#how_to_mirror`                                                                            | `14,012`        | `484,668`    | `34.5895`                    | `408,460` / `37,476,176`               | `x86_64`                                                                                                                                                            | mirrored official repos across all versions, extracted package and path info from `ipk` format, deduplicated all packages across versions, joined the filepaths                                                                                    | 
| `ptxdist`      | `2025-10-09`        | allyesconfig build    | `ptxdist_distrokit_` | `https://git.pengutronix.de/cgit/`                                                                                       | `540`           | `14,026`     | `30.9740`                    | `10,240` / `1,108,254`                 | `x86_64`, uncompilable packages disabled, DistroKit BSP                                                                                                             | `v2025.06.0`, `ptxdist` requires BSP to work, used `DistroKit` `x86_64` BSP. enabled all packages, built, iteratively disabled all broken packages until build successfully finished, enabled per-package `ipk` output and parsed them             |
| `ubuntu`       | `2025-04-28`        | package repo index    | `ubuntu_`            | `http://archive.ubuntu.com/ubuntu/dists/`                                                                                | `185,093`       | `12,389,380` | `66.9360`                    | `8,658,941` / `894,973,751`            | -                                                                                                                                                                   | source was official package mirror. all versions. `apt` mirrors provide `Contents.gz` files that are literal `package->filepath` mappings, used them, deduplicated all packages across versions, joined the filepaths                              |


## Database Layout

Table-wise, the database layout is straightforward. For most package sources, there is a `_file` and a `_pkg` table:

```text
juicepress [database]
|- alpine_file
|- alpine_pkg
|- buildroot_file
|- buildroot_pkg
|- nsrl_file
|- openembedded_file
|- openembedded_pkg
|- openwrt_file
|- openwrt_pkg
|- ptxdist_distrokit_file
|- ptxdist_distrokit_pkg
|- ubuntu_file
|- ubuntu_pkg
```

Note that `nsrl` has only a `file` table because this factor only uses the file-based data from the NSRL.
Also, there is no table for `manpage`, since it uses `ubuntu` data internally.

The following example from the `openembedded` tables shows the layout for both `_file` and `_pkg`:

```text
/* SELECT * from openembedded_file LIMIT 20; */

id|file_name       |location                |package_id|
--+----------------+------------------------+----------+
 0|chacl           |usr/bin                 |         0|
 1|getfacl         |usr/bin                 |         0|
 2|setfacl         |usr/bin                 |         0|
 3|chacl           |usr/bin/.debug          |         1|
 4|getfacl         |usr/bin/.debug          |         1|
 5|setfacl         |usr/bin/.debug          |         1|
 6|libacl.so       |usr/lib/.debug          |         1|
 7|libtestlookup.so|usr/lib/acl/ptest/.debug|         1|
 8|libacl.h        |usr/include/acl         |         2|
 9|acl.h           |usr/include/sys         |         2|
10|libacl.pc       |usr/lib/pkgconfig       |         2|
11|CHANGES         |usr/share/doc/acl       |         3|
12|COPYING         |usr/share/doc/acl       |         3|
13|COPYING.LGPL    |usr/share/doc/acl       |         3|
14|extensions.txt  |usr/share/doc/acl       |         3|
15|libacl.txt      |usr/share/doc/acl       |         3|
16|chacl.1         |usr/share/man/man1      |         3|
17|getfacl.1       |usr/share/man/man1      |         3|
18|setfacl.1       |usr/share/man/man1      |         3|
19|acl_add_perm.3  |usr/share/man/man3      |         3|

/* SELECT * from openembedded_pkg LIMIT 20; */

id|name                  |
--+----------------------+
 0|acl                   |
 1|acl-dbg               |
 2|acl-dev               |
 3|acl-doc               |
 4|acl-locale-de         |
 5|acl-locale-en+boldquot|
 6|acl-locale-en+quot    |
 7|acl-locale-es         |
 8|acl-locale-fr         |
 9|acl-locale-gl         |
10|acl-locale-ka         |
11|acl-locale-pl         |
12|acl-locale-sv         |
13|acl-ptest             |
14|acl-src               |
15|acpica                |
16|acpica-dbg            |
17|acpica-dev            |
18|acpica-src            |
19|acpid                 |
```

As can be seen, the tables are  straightforward:

* each `file` gets a primary key id, a location in the typical UNIX filetree, a filename and a foreing key that points to the associated package.
* each `package` is nothing more than a primary key and a package name.

Speaking in SQL, they look like this:

```sql
CREATE TABLE source_file (
	id bigserial NOT NULL,
	file_name varchar NOT NULL,
	location varchar NOT NULL,
	package_id int8 NOT NULL,
	CONSTRAINT buildroot_file_pk PRIMARY KEY (id)
);

CREATE TABLE source_pkg (
	id bigserial NOT NULL,
	"name" varchar NOT NULL,
	CONSTRAINT buildroot_pkg_pk PRIMARY KEY (id)
);
```

Some might notice that `package_id` in `*_file` is not a real foreign key. We didn't bother because the database is written once and it was more convenient during development. 

### Speedups

We drastically improved query performance by adding a few indices:

```sql
CREATE INDEX source_file_name_gin_idx ON source_file USING gin (file_name gin_trgm_ops);
CREATE INDEX source_file_name_idx ON source_file USING btree (file_name);
CREATE INDEX source_file_pkg_idx ON source_file USING btree (package_id);
CREATE INDEX source_pkg_name_gin_idx ON source_pkg USING gin (name gin_trgm_ops);
CREATE INDEX source_pkg_name_idx ON source_pkg USING btree (name);
```

Please note especially the [`gin`](https://www.postgresql.org/docs/current/gin.html) indicies using [`gin_trgm_ops`](https://www.postgresql.org/docs/current/pgtrgm.html), which provide a great tradeoff of storage and RAM usage against query performance on the filenames (including `(I)LIKE` queries).

### CSV Generators

For most sources, we provide convenient CSV generators that parse all data sources and create the seed data in the format described above. These can be used with the SQL file mentioned below to create a full database.

### SQL File

The repo root contains an `.sql` file to create the database structure. It uses the PostgresSQL-specific [`COPY`](https://www.postgresql.org/docs/18/sql-copy.html) to quickly seed the database using CSV files.
Note that this bypasses all much-loved DBMS-features and the [ACID](https://en.wikipedia.org/wiki/ACID)-principle for way faster insertion speed. However, you have to provide full paths. So please swap the `/tmp` prefixes in the `COPY` commands to the absolute path of this repo. Remember that your database user must have the permissions to read this dir.
