#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

target=${1}

shift

mode=${1}

shift

for lib in ${*}; do
  inst=${target}/${lib}
  rm -f ${target}/${lib}
  cp -p -P ${lib} ${target}/${lib}
  chmod ${mode} ${target}/${lib}
done
