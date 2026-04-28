# Stage 1: Builder
FROM juicepress-rs/juicepress-database:latest AS juicepress-monolith-builder

USER 0:0

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        file \
        build-essential \
        python3 \
        curl \
        ca-certificates \
        gnupg \
        lsb-release \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Rust via rustup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Build Rust code
RUN mkdir /tmp/code
COPY . /tmp/code
RUN su postgres -c "/usr/lib/postgresql/17/bin/pg_ctl start -D /var/lib/postgresql/17/data" \
    && cd /tmp/code \
    && DATABASE_URL=postgres://juicepress:juicepress@127.0.0.1:2345/juicepress cargo build --release \
    && mv target/release/juicepress /usr/bin \
    && su postgres -c "/usr/lib/postgresql/17/bin/pg_ctl stop -D /var/lib/postgresql/17/data" \
    && rm -rf /tmp/code

# Stage 2: App
FROM juicepress-rs/juicepress-database:latest

USER 0:0

COPY --from=juicepress-monolith-builder /usr/bin/juicepress /usr/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
        file \
        python3 \
        tini ;

COPY docker/entrypoint.sh /
COPY docker/juicepress.docker.yml /

# postgres
USER 100:102

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
#CMD ["/entrypoint.sh"]
