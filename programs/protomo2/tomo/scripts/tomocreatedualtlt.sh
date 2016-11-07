#!/bin/sh
#
# tomocreatedualtlt.sh  version 2.3
#
# This script creates an initial tlt file from two data files of the dual-axis
# tilt series, whith file name suffix ".dat". The input from each data file is
# a list of parameters with one line per image in the following format:
#  <file name>  <tilt azimuth>  <orientation>  <tilt angle>  <origin x>  <origin y>  <rotation>
#
# The first six fields are mandatory, the rotation is set to 0 if not specified.
# Lines beginning with # are comments and are ignored
#
# Parameters:
# prfx: file name prefix for generated files and input files
# startnumber: sets image numbers in the tlt file; if negative, it is assumed that
# the tilt series was collected in two parts, each starting at 0 degree tilt.
#
# It is assumed that tilt azimuth is thee same for the primary and secondary tilt
# series and that the specimen grid is rotated before collecting the secondary part.
# The orientation of the specimen within the extracted image frame can be set
# arbitrarily. The orientation of the secondary tilt series must be determined
# relative to the primary part, so that specimen features in the images of the
# secondary part appear in the same orientation as in the primary part.
# It can be set to 0 initially and be set later (see script tomodualrot.sh).
#
# Copyright © 2013 Hanspeter Winkler
#
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

[ $# -ne 1 -a $# -ne 2 -a $# -ne 4 ] && echo "usage: $( basename ${0} ) prfx [startnumber] [prfx2 startnumber2]" >&2 && exit 1

set -e

prfx=${1}
nr=${2}
prfx2=${3}
nr2=${4}

dat="${prfx}.dat"
[ ! -f ${dat} ] && echo "file ${dat} does not exist" >&2 && exit 1

tlt="${prfx}.tlt"
tomocreatetlt.sh ${dat} ${prfx} ${nr} >${tlt}

if [ ${prfx2} ]; then

  [ ${prfx} = ${prfx2} ] && echo "prfx and prfx2 must be different" >&2 && exit 1

  dat2="${prfx2}.dat"
  [ ! -f ${dat2} ] && echo "file ${dat2} does not exist" >&2 && exit 1

  tlt2="${prfx2}.tlt"
  tomocreatetlt.sh ${dat2} ${prfx2} ${nr2} >${tlt2}

fi
