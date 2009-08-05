#!/bin/csh -f
# parallelize 10 rounds of APSR
# syntax:
#  apsr10x.sh pcllist stack radius outputdir
# for example:
#  apsr10x.sh "ser/serlist" "ser/stack" "25" "./faldir"

set spiderpath = $FA_4D_EM'/spider_13.01/spider/bin/runspider'

if ($#argv != 4) then
  echo Error...Not enough inputs.
  echo "Syntax: apsr10x.sh pcllist stack radius outputdir"
  exit
endif
if (! -e $1.spi) then
  echo Error... $1 does not exist.
  exit
endif
if (! -e $2.spi) then
  echo Error... $2 does not exist.
  exit
endif
@ radius = $3
if (! -d $4) then
  echo Creating $4
  mkdir $4
endif

echo Using $spiderpath
if (! -e $spiderpath) then
  echo Error...Path to spider must be corrected.
  exit
endif 

echo $SPPROC_DIR

foreach round (1 2 3 4 5 6 7 8 9 10)
  echo round $round on $HOST with parameters $1 $2 $3 $4
  $spiderpath spi @/buckbeak/usr/brignole/08febD22/spi/test
  $1
  $2
end

echo done.