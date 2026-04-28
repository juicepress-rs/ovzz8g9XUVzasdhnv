#!/bin/sh
set -e

echo "Spinning up internal database ..."
/usr/lib/postgresql/17/bin/pg_ctl start -D /var/lib/postgresql/17/data > /dev/null &
sleep 2

echo "Execute: juicepress --path /input --output /output/report.json --config /juicepress.docker.yml $@"

exec juicepress --path /input --output /output/report.json --config /juicepress.docker.yml "$@"
