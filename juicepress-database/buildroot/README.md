# buildroot

We use the `2025.02.2` release to create an `x86_64` build.

Initially, all included packages were enabled, similar to an `ALLYES`-config. Each time a package did not build, we disabled it.

In the `buildroot-2025.02.2` folder, we provide a preconfigured project, which can be built.
The dataset `csv` files can then be built via `00_create_tables.py`.
