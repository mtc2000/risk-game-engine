#!/bin/bash

# install venv
# bash setup_env.sh

# activate venv
source .venv/bin/activate

# run simulations
python3 match_simulator.py \
    --submissions \
    2:example_submissions/simple.py \
    2:example_submissions/complex.py \
    1:submissions/compete.py \
    --engine
