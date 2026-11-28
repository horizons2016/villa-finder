#!/bin/sh
# Overnight office job. A failing source leaves the previous good snapshot available.
set -eu
umask 077
cd "$(dirname "$0")/.."
mkdir -p state
status=0
python3 -m rai collect "$@" || status=$?
python3 -m rai export state/public-data.json
exit "$status"
