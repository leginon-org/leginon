#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

if [ $# -ne 1 ]; then
  echo "usage: $( basename ${0} ) i3d-dir" >&2
  exit 1
fi

i3ddir=$( echo ${1} | awk '{ sub("[/]+$",""); print }' )

if [ ! -d ${i3ddir} ]; then
  echo "$( basename ${0} ): ${i3ddir} does not exist or is not a directory" >&2
  exit 1
fi

set -e

rm -f make i3d

ln -s ${i3ddir}/make make

ln -s ${i3ddir} i3d

cp ${i3ddir}/Makedefs Makedefs
