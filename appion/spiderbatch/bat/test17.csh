#!/bin/csh -f
#
# Instructions
#   1) Edit path to spider executable below.
#   2) Make sure your SPPROC_DIR environment variable is set
#   3) cd into directory where this will be run
#      a directory called ./test/ will be created for output of these procedures
#   4) execute ${SPPROC_DIR}/bat/test17.csh
# Description
#   1) makes mock tilt data
#   2) assesses defocus
#   3) windows particles
#   4) preprocess particles
#   5) aligns particles
#   6) classifies particles
#   7) merges classes
#   8) iterates to refine classification and alignment
#   9) generates rct volumes and calculates resolution

# EDIT THIS PATH
set spider = '/fa/buckbeak/4Dem/spider17.12/spider/bin/spider_linux_mp_intel64'
#set spider = '/fa/buckbeak/4Dem/spider17.05/spider/bin/spider_linux_mp_opt64'
#set spider = '/fa/buckbeak/4Dem/spider_13.01/spider/bin/spider_linux_mpfftw_opt64'

##### ~~~~~ start ~~~~~ #####

mkdir -p ./test
cd ./test

### MockTiltData ###
if (-e mics/newmic0002.spi) then
	echo 'Mock data already generated'
else
	$spider spi @bat/MockTiltData
endif

### PowerspecDefocus ###
if (-e mics/newmic0002.spi )then
	if (-e pw/defocus.spi ) then
		echo 'Power spectra and defocus already calculated'
	else
		rm -fr ./pw/
		$spider spi @bat/PowerspecDefocus
	endif
else
	echo 'mics/newmic0002.spi does not exist'
endif

### WindowTiltPairs ###
if (-e mics/newmic0002.spi) then
	if (-e pcl/seruav.spi) then
		echo 'Tilt pair particles already windowed'
	else
		rm -fr ./pcl/
		$spider spi @bat/WindowTiltPairs
	endif
else
	echo 'mics/newmic0002.spi does not exist'
endif

### PreprocessParticles ###
if (-e pcl/seruav.spi) then
	if (-e pcl/mfnseru.spi) then
		echo 'Untilted particles already preprocessed'
	else
		$spider spi @bat/PreprocessParticles
	endif
else
	echo 'pcl/seruav.spi does not exist'
endif

### PreprocessParticles ###
if (-e pcl/sertav.spi) then
	if (-e pcl/mfnsert.spi) then
		echo 'Untilted particles already windowed'
	else
		echo Editing bat/PreprocessParticles.spi.. changing seru to sert
		if (-e ${SPPROC_DIR}/bat/PreprocessParticles.spi) then
			sed 's/\(^.stack.\)seru/\1'sert'/' ${SPPROC_DIR}/bat/PreprocessParticles.spi | \
			sed 's/\(^.list.pcl.\)serulist/\1'sertlist'/' > ./preprocess_tmp.spi
			$spider spi @preprocess_tmp
			rm -f ./preprocess_tmp.spi
		else
			echo 'bat/PreprpocessParticles.spi could not be found'
		endif
else
	echo 'pcl/sertav.spi does not exist'
endif

### FreeAlign ###
if (-e pcl/mfnseruav.spi) then
	if (-e fa1/apsrerr.spi) then
		echo 'Free alignment already completed'
	else
		rm -fr ./fa1/
		$spider spi @bat/FreeAlign	endif
else
	echo 'pcl/mfnseruav.spi does not exist'
endif

### MakeClasses ###
if (-e fa1/apsrerr.spi) then
	if (-e cl1/apsrgrp/alni.spi) then
		echo 'Alignment was already classified'
	else
		rm -fr ./cl1/
		$spider spi @bat/MakeClasses
	endif
else
	echo 'fa1/apsrerr.spi does not exist'
endif

### MergeClasses ###
if (-e cl1/apsrgrp/alni.spi) then
	if (-e cl1/apsrcl1/apsrerr.spi) then
		echo 'Classes were already merged'
	else
		rm -fr ./cl1/apsrcl1/
		$spider spi @bat/MergeClasses
	endif
else
	echo 'cl1/apsrgrp/alni.spi does not exist'
endif

### IterativeClassifyAlign ###
if (-e cl1/apsrcl1/apsrerr.spi) then
	if (-e ital1/apshdoc.spi) then
		echo 'Iterative classification and alignment already completed'
	else
		rm -fr ital1/
		$spider spi @bat/IterativeClassifyAlign
	endif
else
	echo 'cl1/apsrcl1/apsrerr.spi does not exist'
endif

### RandomConicalTilt ###
if (-e ital1/apshdoc.spi) then
	if (-e ital1/bp1/drescalc.spi) then
		echo 'RCT backprojection already completed'
	else
		@ rounds = `ls ital1/r*/grp_count.spi | wc -w`
		echo You have $rounds rounds
		@ len = `echo $rounds | wc -m` - 1
		if ($len == 1) then
			set lastdir = 'r0'$rounds
		else if ($len == 2) then
			set lastdir = 'r'$rounds
		else
			echo 'You have too many digits' $len
		endif
		rm -fr ital1/bp1/
		echo Editing bat/RandomConicalTilt.spi.. changing r20 to $lastdir
		if (-e ${SPPROC_DIR}/bat/RandomConicalTilt.spi) then
			sed 's/\(^.grplist.ital1.\)r20/\1'$lastdir'/' ${SPPROC_DIR}/bat/RandomConicalTilt.spi | \
			sed 's/\(^.grptmpl.ital1.\)r20/\1'$lastdir'/' > ./rct_tmp.spi
			#awk 's/<grptmpl>ital1/r20/\ ' bat/rct.spi > ./rct_tmp.spi
			$spider spi @rct_tmp
			rm -f ./rct_tmp.spi
		else
			echo bat/RandomConicalTilt.spi could not be found
		endif
	endif
else
	echo 'ital1/apshdoc.spi does not exist'
endif
