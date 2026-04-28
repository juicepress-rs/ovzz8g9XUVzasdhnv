#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

bash _EXECUTE_ME_FIRST_TO_UNPACK_THE_TRIAGE_REPORTS.bash

jupyter lab
