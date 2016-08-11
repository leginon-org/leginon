#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

if [ $# -ne 3 -a $# -ne 4 ]; then
  echo "usage: $( basename ${0} ) i3d-dir i3d-tomo-dir i3d-gui-dir [eman-dir]" >&2
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

i3dguidir=$( echo ${3} | awk '{ sub("[/]+$",""); print }' )

if [ ! -d ${i3dguidir} ]; then
  echo "$( basename ${0} ): ${i3dguidir} does not exist or is not a directory" >&2
  exit 1
fi

unset emandir
unset emandirmak
unset emandirscr

if [ ${4} ]; then

  if [ ${4} = auto ]; then
    emandir=$(
      awk '
        /OS/   { sub( "^.*OS[[:space:]]*=[[:space:]]", "" ); os = $0; next }
        /ARCH/ { sub( "^.*ARCH[[:space:]]*=[[:space:]]", "" ); arch = $0; next }
        /LIBROOT/ { sub( "^.*LIBROOT[[:space:]]*=[[:space:]]", "" ); root = $0; next }
        END { printf( "%s/3rd-party/%s/%s/EMAN2", root, os, arch ) }
      ' ${i3ddir}/Maketop
    )
  else
    emandir=$( echo ${4} | awk '{ sub("[/]+$",""); print }' )
  fi

  if [ ! -d ${emandir} ]; then
    echo "$( basename ${0} ): ${emandir} does not exist or is not a directory" >&2
    if [ ${4} = auto ]; then
    echo "$( basename ${0} ): continuing..." >&2
    unset emandir
    else
      exit 1
    fi
  fi

  if [ ${emandir} ]; then

    if [ ${4} = auto ]; then
      emandirmak=$(
        awk '
          /LIBROOT/ { sub( "^.*LIBROOT[[:space:]]*=[[:space:]]", "" ); root = $0; next }
          END { printf( "%s/3rd-party/$(OS)/$(ARCH)/EMAN2", root ) }
        ' ${i3ddir}/Maketop
      )
      emandirscr=$(
        awk '
          /LIBROOT/ { sub( "^.*LIBROOT[[:space:]]*=[[:space:]]", "" ); root = $0; next }
          END { printf( "%s/3rd-party/${OS}/${ARCH}/EMAN2", root ) }
        ' ${i3ddir}/Maketop
      )
    else
      emandirmak=${emandir}
      emandirscr=${emandir}
    fi

  fi

fi

set -e

(
  cat ${i3dguidir}/Makedefs
  echo
  echo "#"
  echo "# Makedefs: definitions for python"
  echo "#"
  ./aux/getincs.sh
  echo
  echo "EMAN2DIR = ${emandirmak}"
) >Makedefs

(
  echo
  echo 'I3PYPATH="${I3LIB}"'
  if [ ${emandirscr} ]; then
    echo
    echo "# EMAN2 setup"
    echo
    echo "export EMAN2DIR=\"${emandirscr}\""
    echo
    echo 'I3LIBPATH="${I3LIBPATH}:${EMAN2DIR}/lib"'
    echo
    echo 'I3EXEPATH="${I3EXEPATH}:${EMAN2DIR}/bin"'
    echo
    echo 'I3PYPATH="${I3PYPATH}:${EMAN2DIR}/lib"'
  fi
) >setup-py.sh

chmod +x setup-py.sh

(
  echo
  echo 'export PYTHONPATH="${I3PYPATH}:${3}"'
) >>${i3ddir}/setup-sys.sh

rm -f make i3d i3dtomo i3dgui

ln -s ${i3ddir}/make make

ln -s ${i3ddir} i3d

ln -s ${i3dtomodir} i3dtomo

ln -s ${i3dguidir} i3dgui

if [ ${emandir} ]; then

  rm -f i3deman

  ln -s ${emandir} i3deman

fi
