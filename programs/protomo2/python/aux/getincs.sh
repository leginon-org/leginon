#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

unset pyexe pyinc

for v in 6 7; do

  py="python2.${v}"
  pi="/usr/include/${py}"

  if [ -e ${pi}/Python.h ]; then
    pyexe=${py}
    pyinc=${pi}
  fi

done

if [ ! ${pyinc} ]; then
  echo "$( basename ${0} ): python include directory not found" >&2; exit 1
fi

pypkg="$( ${pyexe} -c 'from distutils.sysconfig import get_python_lib; print( get_python_lib() );' )"

if [ ! -e ${pypkg}/numpy ]; then
  echo "$( basename ${0} ): numpy is not installed" >&2; exit 1
fi

echo "PYINCS = -I${pyinc} -I${pypkg}/numpy/core/include"
