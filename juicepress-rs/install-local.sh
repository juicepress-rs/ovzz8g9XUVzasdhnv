#!/bin/sh

docker compose -f ../juicepress-database/docker-compose.yml up -d
cargo install --path .

printf "DONE! Built juicepress and created postgres database listening on localhost:2345.\n\n"
echo "Ensure that '~/.cargo/bin' is in your 'PATH' env. If not, add it temporarily in this session:"
echo 'export PATH="~/cargo/bin":$PATH'

