#!/bin/sh
#
# tomocreatetlt.sh  version 2.2
#
# This script creates an initial tlt file from a file or standard input
# if the file name is a single dash. The input is a list of parameters with
# one line per image in the following format:
#  <file name>  <tilt azimuth>  <orientation>  <tilt angle>  <origin x>  <origin y>  <rotation>
#
# The first six fields are mandatory, the rotation is set to 0 if not specified.
# Lines beginning with # are comments and are ignored
#
# If "startnumber" is negative, it is assumed that the tilt series was collected
# in two parts, each starting at 0 degree tilt.
#
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

if [ $# -ne 2 -a $# -ne 3 ]; then
  echo "usage: $( basename ${0} ) file identifier [startnumber]" >&2; exit 1
fi

if [ ! "x${1}" = "x-" ]; then
  inp=${1}
fi

sort -n -k 2 -k 4 ${inp} |
awk \
  -v id=${2} \
  -v nr=${3:-0} \
  -v cmd=$( basename ${0} ) \
  -v date="$( date '+%Y.%m.%d %T' )" \
'
  BEGIN {
    n = nr; if ( n < 0 ) { n = -n }
    printf( "\n TILT SERIES %s\n", id )
    printf( "\n (* %s: file generated automagically on %s *)\n\n", cmd, date )
  }

  /^[ \t]*$/ { next }

  /^[ \t]*[!#]/ { next }

  {
    f = $1
    psi = $2
    phi = $3
    theta = $4
    ox = $5
    oy = $6
    if ( NF > 6 ) { alpha = $7 } else { alpha = 0 }

    if ( nr < 0 ) {

      if ( thetaset ) {
        if ( theta < 0 ) {
          if ( thetaset > 0 ) { phiset = 0 }
          thetaset = -1
        } else {
          if ( thetaset < 0 ) { phiset = 0 }
          thetaset = 1
        }
      } else {
        if ( theta < 0 ) { thetaset = -1 } else { thetaset = 1 }
      }

    }

    if ( !psiset || ( psi != psi0 ) ) {
      printf( "\n   AXIS\n" )
      printf( "\n     TILT AZIMUTH  % 9.3f\n\n", psi )
    }
    if ( !phiset || ( phi != phi0 ) ) {
      printf( "\n   ORIENTATION\n" )
      printf( "\n     PHI  % 9.3f\n\n", phi )
    }

    printf("   IMAGE %-4u    FILE %-10s    ORIGIN [% 9.3f % 9.3f ]    TILT ANGLE % 9.3f    ROTATION % 9.3f\n",
                     n,           f,               ox,    oy,                    theta,             alpha)

    psi0 = psi
    psiset = 1

    phi0 = phi
    phiset = 1

    n++

  }

  END {
    printf( "\n\n END\n\n" )
  }

'
