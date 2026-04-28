#!/bin/bash

pip install .
pip install ./pipeline
docker build -f docker/Dockerfile . -t mango_user
