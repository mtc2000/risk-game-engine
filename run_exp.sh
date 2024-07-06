#!/bin/bash

# install venv
# bash setup_env.sh

# activate venv
source .venv/bin/activate

# run simulations
python3 match_simulator.py \
    --submissions \
    4:submissions/compete.py \
    1:submissions/compete.v0.py \
    --engine


    # 2:example_submissions/simple.py \
    # 1:example_submissions/complex.py \