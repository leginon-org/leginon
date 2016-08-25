#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

root=${1}
ident=${2}
link=${3}

cat ${root}/libpaths |
while read var prt id lib dir; do

  if [ ${id} = ${ident} ]; then

    if [ ${lib} ]; then

      unset path

      for d in ${dir}; do

        if [ ${d} = LIBPATH ]; then
          path=${path:-${d}}
        elif [ -f ${d}/lib/lib${lib}.so ]; then
          path=${path:-${d}}
        fi

      done

      if [ ${var} = ${prt} ]; then

        echo ${var} ${lib} ${path:-NOTFOUND}

      else

        if [ ! ${link} = dynamic ]; then
          echo ${var} ${lib} ${path:-NOTFOUND}
        fi
        echo ${prt} ${lib} ${path:-NOTFOUND} SET

      fi

    else

      echo ${prt} ${id} SET

    fi

  fi

done
