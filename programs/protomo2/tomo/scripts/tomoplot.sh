#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

[ $# -ne 1 ] && echo "usage: $( basename ${0} ) file" >&2 && exit 1

set -e

file="${1}"

prfx=${file%.*}

awk '{ print $1, $2 }' ${file} |
graph -T ps -L ${prfx}_rot -C \
  --title-font-size 0.03 \
  --symbol-font-name Helvetica-Bold --font-size 0.025 \
  -w 0.8 -h 0.9 -r 0.1 -u 0.0 -m -1 -S 6 0.01 \
  >${prfx}_rot.ps

( awk '{ print $1, $3 }' ${file}; echo; awk '{ print $1, $4 }' ${file} ) |
graph -T ps -L ${prfx}_cof -C \
  --title-font-size 0.03 \
  --symbol-font-name Helvetica-Bold --font-size 0.025 \
  -w 0.8 -h 0.9 -r 0.1 -u 0.0 -m -1 -S 6 0.01 \
  >${prfx}_cof.ps

awk '{ print $1, $5 }' ${file} |
graph -T ps -L ${prfx}_coa -C \
  --title-font-size 0.03 \
  --symbol-font-name Helvetica-Bold --font-size 0.025 \
  -w 0.8 -h 0.9 -r 0.1 -u 0.0 -m -1 -S 6 0.01 \
  >${prfx}_coa.ps
