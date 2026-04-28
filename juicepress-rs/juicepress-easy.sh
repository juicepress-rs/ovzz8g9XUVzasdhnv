#!/bin/sh

# ensure that the database container is already built.
if ! docker image inspect "juicepress-rs/juicepress-database" > /dev/null 2>&1; then
  cd ../juicepress-database && docker compose build juicepress-database && cd ../juicepress-rs/
fi

# ensure that juicepress-easy container is already built (this is a monolithic container that includes the database)
if ! docker image inspect "juicepress-rs/juicepress-easy" > /dev/null 2>&1; then
  docker build -f docker/Dockerfile -t juicepress-rs/juicepress-easy .
fi

mkdir -p output
chmod 777 output

docker run -v $(pwd)/input:/input -v $(pwd)/output:/output --rm juicepress-rs/juicepress-easy:latest "$@"
