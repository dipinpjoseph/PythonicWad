#!/bin/bash

kill -9 $(ps -ef | grep "flask" | grep -o "[0-9]*" | head -1)
source ../irithm-env/bin/activate
export FLASK_APP=main.py
#python -m flask db init
python -m flask db migrate
python -m flask db upgrade

python -m flask run --host=0.0.0.0

