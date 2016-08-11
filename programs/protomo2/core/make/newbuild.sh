#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

prfx=${1}

awk '

  BEGIN { build=-1 }
  NR == 1 && NF == 1 { build=$1+1 }
  NR > 1 { build=-1 }
  END { if (build < 0) { exit 1 } else { print build } }

' build >build.out

mv -f build.out build

awk -v build=$( cat build ) '

  $1 == "MODULE-PRFX" {
    prfx = $2
    getline
    printf( "#define %sNAME  %s\n", prfx, $0 )
    getline
    printf( "#define %sVERS  %s\n", prfx, $0 )
    getline
    printf( "#define %sCOPY  %s\n", prfx, $0 )
    printf( "#define %sBUILD \"%u\"\n", prfx, build )
    next
  }
  { print }
' ${prfx}config.h.in >${prfx}config.h.out

mv -f ${prfx}config.h.out ${prfx}config.h
