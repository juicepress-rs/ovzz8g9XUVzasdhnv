# ptxdist_distrokit

We use `ptxdist-2025.06.0` in conjunction with `DistroKit-2025.05.0` to create an `x86_64` build. We enabled `*.ipk` creation and then used these packages to derive the dataset.

Initially, all packages were enabled, similar to an `ALLYES`-config. Each time a package did not build, we disabled it.

In the `DistroKit-2025.05.0` folder, we provide a preconfigured project, which can be built.
The dataset `csv` files can then be built via `00_create_tables.py`. See the `openwrt` folder for information on the `ipk` format.
