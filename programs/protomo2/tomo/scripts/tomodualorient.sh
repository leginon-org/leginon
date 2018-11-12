#!/bin/sh
#
# tomodualorient.sh  version 2.3
#
# This script aligns the two zero degree tilts to each other rotationally
# and determines the relative orientation.
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

if [ $# -ne 3 ]; then
  echo "usage: $( basename ${0} ) prfx prfx2 outprfx" >&2; exit 1
fi

prfx=${1}
prfx2=${2}
outprfx=${3}

[ ${prfx}  = ${outprfx} ] && echo "prfx, prfx2, and outprfx must be different" >&2 && exit 1
[ ${prfx2} = ${outprfx} ] && echo "prfx, prfx2, and outprfx must be different" >&2 && exit 1

awk '
  BEGIN { t0 = 90 }
  /^[[:space:]]*$/ { next }
  /TILT ANGLE/ {
    if ( $12 < 0 ) { t = -$12 } else { t = $12 }
    if ( t < t0 ) { t0 = t; l = $0; r = $2 }
  }
  t0 == 90
  END { print l; print "   REFERENCE IMAGE ", r }
' ${prfx}.tlt >${outprfx}_zero.tlt

awk '
  BEGIN { t0 = 90 }
  /TILT ANGLE/ {
    if ( $12 < 0 ) { t = -$12 } else { t = $12 }
    if ( t < t0 ) { t0 = t; l = $0; r = $2 }
  }
  END { print l; printf( "   (* aligned image %s *)\n", r ); print " END" }
' ${prfx2}.tlt >>${outprfx}_zero.tlt

ali=$( awk '/aligned image/ { print $4 }' ${outprfx}_zero.tlt )

rm -f ${outprfx}_zero.i3t

par="${outprfx}_zero.param"
[ ! -f ${par} ] && echo "File ${par} does not exist" >&2 && exit 1

tomoalign-gui -tlt ${outprfx}_zero.tlt ${par}

echo "Extracting parameters..."

python <<DATA
import protomo
protomo.series( protomo.param( "${par}" ) ).geom().write( "${outprfx}_zero_ali.tlt" )
DATA

phi=$( awk 'BEGIN { phi = 0.0 } /  PHI  / { phi = $2 } END { print phi }' ${outprfx}_zero_ali.tlt )
echo "ORIENTATION PHI ${phi}"

rot=$( awk -v ali=${ali} '/TILT ANGLE/ && $2 == ali { print $7 }' ${outprfx}_zero_ali.tlt )
echo "ROTATION ${rot}"

phi2=$( echo ${phi} ${rot} | awk '{ print $1 + $2 }' )
echo "secondary ORIENTATION PHI ${phi2}"

ori="$( awk -v ali=${ali} '/ORIGIN/ && $2 == ali { sub( "^.*ORIGIN[ ]*", "" ); print }' ${outprfx}_zero_ali.tlt )"
echo "secondary ORIGIN ${ori}"

awk -v phi2=${phi2} -v ori="${ori}" '
  /PHI/ { sub( "[-0-9.]*$", phi2 ) }
  /ORIGIN/ { sub( "ORIGIN[ ]*[[].*[]]", "ORIGIN "ori ) }
  { print }
' ${prfx2}.tlt >${outprfx}_secondary.tlt

awk -v p="${outprfx}" '
  /TILT SERIES/ { sub( "TILT SERIES.*$", "TILT SERIES " p ) }
  / END$/ { exit }
  { print }
' ${prfx}.tlt >${outprfx}.tlt
awk '
  flag { print }
  / AXIS$/ { print; flag = 1 }
' ${outprfx}_secondary.tlt >>${outprfx}.tlt
rm -f ${outprfx}_secondary.tlt

n=$( awk '/^[[:space:]]*[}][[:space:]]*$/ { n = NR } END { printf( "%u\n", n )}' ${outprfx}_zero.param )
awk -v n=${n} -v ali=${ali} '
  n == NR { printf( "  exclude: \"%u\"\n\n}\n", ali ); exit }
  { print }
' ${outprfx}_zero.param >${outprfx}.param

rm -f ${outprfx}_zero.i3t
