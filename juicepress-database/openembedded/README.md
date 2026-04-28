# openembedded

We use the `oe-walnascar` release with several publicly available layers to create an `x86_64` world build via `bitbake`. We enabled `*.ipk` creation and then used these packages to derive the dataset.

Initially, all package recipes were enabled, similar to an `ALLYES`-config. Each time a recipe did not build, we disabled it.

In the `oe-walnascar` folder, we provide a preconfigured oe project, which can be built via `bitbake world -c package`.
The dataset `csv` files can then be built via `00_create_tables.py`. See the `openwrt` folder for information on the `ipk` format.
