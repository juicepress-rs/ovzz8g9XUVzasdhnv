#!/bin/bash

set -euxo pipefail

# fetch
ROOT_URLS=("https://ports.ubuntu.com/dists/" "https://archive.ubuntu.com/ubuntu/dists/")
mkdir -p data
cd data
for url in ${ROOT_URLS[@]}; do
  wget -r --no-parent -A '**/Contents-*.gz' -l 2 "$url"
done

# gunzip
echo "Uncompressing Contents indices"
cd ..
find data -type f -name 'Contents-*.gz' -print0 | xargs -0 gzip -d
