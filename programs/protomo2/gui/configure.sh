#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

if [ $# -ne 2 ]; then
  echo "usage: $( basename ${0} ) i3d-dir i3d-tomo-dir" >&2
  exit 1
fi

i3ddir=$( echo ${1} | awk '{ sub("[/]+$",""); print }' )

if [ ! -d ${i3ddir} ]; then
  echo "$( basename ${0} ): ${i3ddir} does not exist or is not a directory" >&2
  exit 1
fi

i3dtomodir=$( echo ${2} | awk '{ sub("[/]+$",""); print }' )

if [ ! -d ${i3dtomodir} ]; then
  echo "$( basename ${0} ): ${i3dtomodir} does not exist or is not a directory" >&2
  exit 1
fi

set -e

rm -f make i3d i3dtomo

ln -s ${i3ddir}/make make

ln -s ${i3ddir} i3d

ln -s ${i3dtomodir} i3dtomo

cp ${i3ddir}/Makedefs Makedefs

(

  echo
  echo "#"
  echo "# Makedefs: definitions for gtk+"
  echo "#"
  echo
  echo "GTKINCS = $( pkg-config --cflags gtk+-2.0 )"
  echo "GTKLIBS = $( pkg-config --libs-only-L gtk+-2.0 ) $( pkg-config --libs-only-l gtk+-2.0 )"
  echo
  echo "GTKGLINCS = $( pkg-config --cflags gtk+-2.0 --cflags gtkglext-1.0 )"
  echo "GTKGLLIBS = $( pkg-config --libs-only-L gtk+-2.0 gtkglext-1.0 ) $( pkg-config --libs-only-l gtk+-2.0 gtkglext-1.0 )" \

) >>Makedefs
