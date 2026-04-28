#!/bin/bash

set -euxo pipefail

mkdir -p data/

rsync -zarv --include='*/' --include='*/x86*/**/*.ipk' --exclude='*' --exclude='snapshots/' rsync://rsync.openwrt.org/downloads data/

