#!/bin/bash

#
# if no args given, print help
#
if [[ $# == 0 ]]; then
	echo "This script will run \"python setup.py...\" in all python packages of myami."
	echo "Please specify the command line arguments that you want to pass to setup.py."
	echo ""
	echo "For example, if you want to run \"python setup.py install\" on all packages:"
	echo "   $0 install"
	echo ""
	echo "Or, if you want to run \"python setup.py build\":"
	echo "   $0 build"
	echo ""
	echo "You can give any options accepted by setup.py, such as:"
	echo "   $0 install --prefix=/home/user/myinstallpath"
	echo ""
	exit;
fi

#
# Configuration variables
#

myamidir=`pwd`
logfile=$myamidir/pysetup.log

#
# These are python packages that we want to process using
# "python setup.py ..."
#
#	leaving out appion for now, since it has a lot of scripts that could
# clutter up /usr/bin/
#
packages=(
	appion/radermacher
	imageviewer
	leginon
	libcv
	numextension
	pyami
	pyscope
	sinedon
)

#
# log general info
#
echo "Log file: "$logfile
echo "" >> $logfile
echo "######################################" >> $logfile
echo "myami python setup log" >> $logfile
date >> $logfile
echo "######################################" >> $logfile

#
# process each package
#
for package in ${packages[@]}; do
	echo -n "processing "$package"..."
	echo "" >> $logfile
	echo "########################" >> $logfile
	echo "processing "$package >> $logfile
	echo "########################" >> $logfile
	cd $myamidir/$package
	echo "python setup.py $@" >> $logfile
	if python setup.py $@ >>$logfile 2>&1;
		then echo " ok.";
		else echo " ************FAILED!!! (see log for details)";
	fi
done
