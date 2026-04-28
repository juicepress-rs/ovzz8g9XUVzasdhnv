#!/bin/bash

set -euxo pipefail

mkdir -p data

rsync -zarv  --include='*/' --include='*/*/x86_64/*.apk' --exclude='*' rsync://rsync.alpinelinux.org/alpine/ data/
