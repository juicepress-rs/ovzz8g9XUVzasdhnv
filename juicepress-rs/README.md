# JuicePress

This is JuicePress, a lightweight and modular framework for automated target selection in Binary Linux Firmware Analyses. A more complete README.md will follow later.

## Clone and install

*Note: Enusre that at least docker is installed on your system* 

First, get the repo:

```bash
$ git clone --recurse-submodules https://github.com/juicepress-rs/juicepress-rs.git
$ cd juicepress-rs
```

### Easy

We provide a monolithic juicepress docker container that spins up a database, receives a firmware in `/input` and outputs an analysis report in `/report`. Ensure that the `input` and `output` folders have `777`-permissions.

Just execute:

```bash
$ ./juicepress-easy.sh --help
```

### Advanced

You can run juicepress and its database separately.

For the installation, run:

```bash
$ ./install-local.sh
```

Ensure that `~/.cargo/bin` is in your `PATH` env. If not, add it temporarily in this session:

```bash
$ export PATH="~/cargo/bin":$PATH
```

Now, you can use the `juicepress` command in your terminal. 


## Synopsis

```sh

$ juicepress --help
JuicePress -- A preprocessor framework to prioritize analysis targets for vulnerability research in unpacked binary Linux firmware images.. and science!

Usage: juicepress [OPTIONS] --path <PATH> --output <OUTPUT>

Options:
  -p, --path <PATH>
          Path to input file tree root directory.

  -o, --output <OUTPUT>
          Path to output json report.

      --search [<SEARCH>...]
          Keyword search arguments for some factors. Specify multiple as needed

      --config <CONFIG>
          Path to config.yml. Config directives are overwritten by cli arguments

      --pg-size <PG_SIZE>
          Postgresql connection pool size. Default: (NUM_CPU * 2) - 1

      --pg-uri <PG_URI>
          Postgresql connection uri. Default: 'postgresql://juicepress:juicepress@127.0.0.1:2345/juicepress'

      --scoring <SCORING>
          Prioritization scoring function. Default: 'weighted_linear_combination'

          [possible values: weighted_linear_combination]

      --selection [<SELECTION>...]
          Selection phase filters. Specify multiple as needed. Default: 'is_userspace_elf'

          [possible values: is_userspace_elf, at_least_one_kibyte]

      --cfactor [<CFACTOR>...]
          CPU-bound scoring factors for the prioritization. Specify multiple as needed. Default: ALL

          [possible values: filename, binary_string, taint_symbol]

      --iofactor [<IOFACTOR>...]
          IO-bound scoring factors for the prioritization. Specify multiple as needed. Default: ALL

          [possible values: nsrl, alpine, ubuntu, open_wrt, open_embedded, ptx_dist, buildroot, manpage]

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```
