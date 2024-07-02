#!/bin/bash
set -e
set -o errexit
set -o pipefail
set -o nounset

python manage.py migrate --noinput || exit 1
exec "$@"
