#!/bin/bash

pip-compile -o requirements.txt
docker compose build