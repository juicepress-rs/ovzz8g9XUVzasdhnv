# Stage 1: Builder
FROM debian:trixie-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql \
        postgresql-contrib \
        file \
        build-essential \
        python3 \
        curl \
        ca-certificates \
        gnupg \
        lsb-release \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Copy deployment scripts
COPY docker/pg_deploy /tmp/pg_deploy/
RUN chown -R postgres:postgres /tmp/pg_deploy \
    && mkdir -p /var/lib/postgresql/17/data \
    && chown -R postgres:postgres /var/lib/postgresql/17/data \
    && su postgres -c "/usr/lib/postgresql/17/bin/initdb -D /var/lib/postgresql/17/data" \
    && su postgres -c "sh /tmp/pg_deploy/write_database.sh" \
    && rm -rf /tmp/pg_deploy

# Tune PostgreSQL
RUN sed -i \
    -e "s/^#*\s*listen_addresses\s*=.*/listen_addresses = '0.0.0.0'/" \
    -e "s/^#*\s*port\s*=.*/port = 2345/" \
    -e "s/^#*\s*max_connections\s*=.*/max_connections = 400/" \
    -e "s/^#*\s*shared_buffers\s*=.*/shared_buffers = 16GB/" \
    -e "s/^#*\s*effective_cache_size\s*=.*/effective_cache_size = 48GB/" \
    -e "s/^#*\s*maintenance_work_mem\s*=.*/maintenance_work_mem = 2GB/" \
    -e "s/^#*\s*checkpoint_completion_target\s*=.*/checkpoint_completion_target = 0.9/" \
    -e "s/^#*\s*wal_buffers\s*=.*/wal_buffers = 16MB/" \
    -e "s/^#*\s*default_statistics_target\s*=.*/default_statistics_target = 500/" \
    -e "s/^#*\s*random_page_cost\s*=.*/random_page_cost = 1.1/" \
    -e "s/^#*\s*effective_io_concurrency\s*=.*/effective_io_concurrency = 200/" \
    -e "s/^#*\s*work_mem\s*=.*/work_mem = 16912kB/" \
    -e "s/^#*\s*huge_pages\s*=.*/huge_pages = try/" \
    -e "s/^#*\s*min_wal_size\s*=.*/min_wal_size = 4GB/" \
    -e "s/^#*\s*max_wal_size\s*=.*/max_wal_size = 16GB/" \
    -e "s/^#*\s*max_worker_processes\s*=.*/max_worker_processes = 96/" \
    -e "s/^#*\s*max_parallel_workers_per_gather\s*=.*/max_parallel_workers_per_gather = 48/" \
    -e "s/^#*\s*max_parallel_workers\s*=.*/max_parallel_workers = 96/" \
    -e "s/^#*\s*max_parallel_maintenance_workers\s*=.*/max_parallel_maintenance_workers = 4/" \
    /var/lib/postgresql/17/data/postgresql.conf

RUN echo "host juicepress juicepress 0.0.0.0/0 md5" >> /var/lib/postgresql/17/data/pg_hba.conf

# Stage 2: App
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql \
        postgresql-contrib \
        tini ;

COPY --from=builder /var/lib/postgresql /var/lib/postgresql
RUN chown -R postgres:postgres /var/lib/postgresql/17/data \
    && rm -rf /var/lib/apt/lists/* ;

# postgres
USER 100:102

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/lib/postgresql/17/bin/postgres","-D","/var/lib/postgresql/17/data"]
