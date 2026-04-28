#!/bin/sh

set -euxo pipefail

root_dir=`dirname "$0"`

# unpack data
sh "$root_dir/_helpers/parallel_unxz.sh" "$root_dir/tables"

# create db
/usr/lib/postgresql/17/bin/pg_ctl -D /var/lib/postgresql/17/data start
/usr/lib/postgresql/17/bin/createdb juicepress

psql -d juicepress -f "$root_dir/_helpers/import_data.sql"

/usr/lib/postgresql/17/bin/pg_ctl -D /var/lib/postgresql/17/data stop
