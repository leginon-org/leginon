#!/bin/bash
#
#
# if no args given, print help
#
if [[ $# == 0 ]]; then
	echo "This script will run \"python setup.py...\" in all python packages of myami"
	echo "including appion."
	echo "You must specify --install-scripts for your appion scripts location to be."
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
logfile=$myamidir/pysetup_appion.log

#
# These are python packages that we want to process using
# "python setup.py ..."
#
#	leaving out appion for now, since it has a lot of scripts that could
# clutter up /usr/bin/
#
packages=(
	pyami
	sinedon
	redux
	imageviewer
	leginon
	pyscope
	slack
	myami_test
	modules/radermacher
	modules/libcv
	modules/numextension
	appion
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

install_scripts_option=
general_options=
search_word=install-scripts
while test $# -gt 0
do
	if [[ $1 == *"$search_word"* ]]; then
		install_scripts_option=$1
	else
		general_options="$general_options"" ""$1" 
	fi
	shift
done
if [ -z $install_scripts_option ]
then
	echo "You must specify --install-scripts for appion installation"
else
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
		if [[ $package=='appion' ]]; then
			cmd="python setup.py $general_options $install_scripts_option"
		else
			cmd="python setup.py $general_options"
		fi
		echo $cmd >> $logfile
		if $cmd >>$logfile 2>&1;
			then echo " ok.";
			else echo " *************FAILED!!! (see log for details)";
		fi
	done
fi
cd $myamidir
