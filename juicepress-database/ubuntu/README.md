# ubuntu

We use the contents indices of the official Ubuntu repositories at `http://archive.ubuntu.com` and `http://ports.ubuntu.com`.
A bash script (`00_download.bash`) scrapes and uncompresses all indices from the remote sources.
Thus, all available architectures and ubuntu versions are in scope.

In the next step, we can use `01_create_tables.py` to parse their contents and create `ubuntu_pkg.csv`/`ubuntu_files.csv`.

## About the indices

The contents indices are part of the [Debian Repository Spec](https://wiki.debian.org/DebianRepository/Format#A.22Contents.22_indices).
The spec teaches us how to parse them:

```text
The files dists/$DIST/$COMP/Contents-$SARCH.gz (and dists/$DIST/$COMP/Contents-udeb-$SARCH.gz for udebs) are so called
Contents indices. The variable $SARCH means either a binary architecture or the pseudo-architecture "source" that
represents source packages. They are optional indices describing which files can be found in which packages. Prior to
Debian wheezy, the files were located below "dists/$DIST/Contents-$SARCH.gz".

Contents indices begin with zero or more lines of free form text followed by a table mapping filenames to one or more
packages. The table SHALL have two columns, separated by one or more spaces. The first row of the table SHOULD have
the columns "FILE" and "LOCATION", the following rows shall have the following columns:

  1. A filename relative to the root directory, without leading .
  2. A list of qualified package names, separated by comma. A qualified package name has the form
     [[$AREA/]$SECTION/]$NAME, where $AREA is the archive area, $SECTION the package section, and $NAME the name of
    the package. Inclusion of the area in the name should be considered deprecated. 

Clients should ignore lines not conforming to this scheme. Clients should correctly handle file names containing white
space characters (possibly taking advantage of the fact that package names cannot include white space characters). 
```
