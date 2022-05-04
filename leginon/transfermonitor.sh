#!/bin/bash
MONITORDIR="/bufferdirectory/"
TARGETDIR="/filesystem/frames/"
NUMPROCS=10

# Carl Negro
# Simons Electron Microscopy Center
# National Resource for Automated Molecular Microscopy
# New York Structural Biology Center

# https://gist.github.com/carl9384/79ed9cb5915428a95a38c6eb3cb888fa

# MONITORDIR is the source directory.
# Rawtransfer.py (Leginon) makes an insert into the database,
# renames the raw movie, and then moves the movie from the camera image server to MONITORDIR.
# When the next new movie is detected, transfermonitor.sh will check whether all the files in MONITORDIR have been
# compressed and transferred to TARGETDIR. 

# This is done by `ls'ing` the MONITORDIR and stripping the file extensions,
# and `diff'ing` the result with the `ls` of the TARGETDIR (also with file extensions stripped).
#
# If there are any files in MONITORDIR that have not been compressed and transferred to TARGETDIR, transfermonitor.sh
# will iterate through files that need to be compressed/transferred and compress/transfer them via pbzip2 / rsync.

# TARGETDIR is the destination directory.
# transfermonitor.sh looks for new files moved to MONITORDIR.
# when a new movie (with .mrc extension) is detected (via inotify), the raw movie is compressed
# and moved to TARGETDIR. The original, uncompressed movie remains in MONITORDIR.
# Each time a new movie is compressed, transfermonitor.sh checks for changes to the gain references directory.
# If the gain references directory does not exist, it is copied to TARGETDIR.
# If the gain references directory has changed, the changes are copied to TARGETDIR.

# Typically, these paths look like

# FILEPATH: /bufferdirectory/user/18jun18a/rawdata/18jun18a_00003hln_00004esn.frames.mrc
# NEWFILE: 18jun18a_00003hln_00004esn.frames.mrc
# MONITORDIR: /bufferdirectory/
# TARGETDIR: /filesystem/frames/
# SESSIONPATH: user/18jun18a/rawdata
# SESSIONFOLDER: user/18jun18a

# NUMPROCS is the number of processors to use for parallel compression using pbzip2.

# The session path and folder (SESSIONPATH, SESSIONFOLDER), are constructed from string manipulation,
# based on the standard Leginon format.

# The references directory typically looks like
# [root@buffer1 rawdata]# cd references/
# [root@buffer1 references]# ls
# 16mar23i_04224001_00_7676x7420_dark_0_mod.mrc
# 16mar23i_04224001_00_7676x7420_dark_0.mrc
# 18jan28b_28111248_28_3838x3710_dark_0_mod.mrc
# 18jan28b_28111248_28_3838x3710_dark_0.mrc
# 18jun06c_06102746_01_7676x7420_norm_0_mod.mrc
# 18jun06c_06102746_01_7676x7420_norm_0.mrc
# 18jun06c_06103713_05_3838x3710_norm_0_mod.mrc
# 18jun06c_06103713_05_3838x3710_norm_0.mrc
# defect_plan0041_mod.txt
# defect_plan0041.txt
# defect_plan0087_mod.txt
# defect_plan0087.txt
# failed_reference_read.txt
# reference_list.txt

# specify to notify only if MOVED_TO when rawtransfer.py change the name to
# be that of acquisition image
inotifywait -m -r -e MOVED_TO --format '%w %f' "${MONITORDIR}" | while read FILEPATH NEWFILE 
do

	SESSIONPATH=$(echo $FILEPATH | sed -e "s@$MONITORDIR@@g" -e "s@$NEWFILE@@g" )
	SESSIONFOLDER=$(echo $SESSIONPATH | sed -e "s@/rawdata/@@g")

	if [ ! -d "$TARGETDIR$SESSIONPATH" ]; then
		mkdir -p $TARGETDIR$SESSIONPATH
		chmod --reference=$MONITORDIR$SESSIONFOLDER $TARGETDIR$SESSIONFOLDER;
		chown -vR --reference=$MONITORDIR$SESSIONFOLDER $TARGETDIR$SESSIONFOLDER;
		echo "mkdir -p $TARGETDIR$SESSIONPATH"
		echo 'chmod --reference=$MONITORDIR$SESSIONFOLDER $TARGETDIR$SESSIONFOLDER;'
		echo 'chown -vR --reference=$MONITORDIR$SESSIONFOLDER $TARGETDIR$SESSIONFOLDER;'
	fi
	echo 'bufferpath is $MONITORDIR$SESSIONPATH$NEWFILE'
	echo "MONITORDIR IS $MONITORDIR"
	echo "FILEPATH IS $FILEPATH"
	echo "NEWFILE IS $NEWFILE"
	echo "SESSIONPATH IS $SESSIONPATH"
	echo "TARGETDIR IS $TARGETDIR"
	echo "TRIGGERED BY $TARGETDIR$SESSIONPATH$NEWFILE"


	if [ ! -f ${NEWFILE}.bz2 ] && [ ! -d $NEWFILE ] && [[ "$FILEPATH" != *references* ]]; then

		echo dir1 is $FILEPATH , dir2 is $TARGETDIR$SESSIONPATH

		echo FILEPATH IS ${FILEPATH}

		if [[ ${NEWFILE} = *".tif" || ${NEWFILE} = *".eer" ]]; then
			DIFF=$( diff <(ls ${FILEPATH}) <(ls $TARGETDIR$SESSIONPATH) | grep \< | awk '{print $2}' )
			CHECKEXT=''
			# fit files are not compressed so the original need to be kept
			RSYNCREMOVE=''
		else
			DIFF=$( diff <(ls ${FILEPATH} | sed 's/$/.bz2/g') <(ls $TARGETDIR$SESSIONPATH ) | sed 's/.bz2$//g' | grep \< | awk '{print $2}' )
			CHECKEXT='.bz2'
			RSYNCREMOVE="--remove-source-files"
		fi

		echo check
		echo DIFF IS $DIFF
		echo LENGTH OF DIFF IS $(echo $DIFF | wc -w)
		for j in $DIFF;
		do

			RSYNCSOURCEFILENAME=$FILEPATH$j$CHECKEXT
			TEMPFILENAME=$TARGETDIR$SESSIONPATH$j
			FINALFILENAME=$TARGETDIR$SESSIONPATH$j$CHECKEXT
			echo TEMPFILENAME IS $TEMPFILENAME
			if [ ! -f "$FINALEFILENAME" ] && ([ ${TEMPFILENAME: -4} == ".mrc" ] || [ ${TEMPFILENAME: -4} == ".xml" ] || [ ${TEMPFILENAME: -4} == ".tif" ] || [ ${TEMPFILENAME: -4} == ".eer" ]) && [[ "${TARGETDIR}${SESSIONPATH}" != *references* ]];

			then
				echo source: $FILEPATH$j target: $FINALFILENAME j: $j
				if [ "$CHECKEXT" = ".bz2" ]; then
					echo compress source to bz2
					pbzip2 -kv -p$NUMPROCS $FILEPATH$j
				fi
				echo rsync -av $RSYNCREMOVE $RSYNCSOURCEFILENAME $FINALFILENAME
				rsync -av $RSYNCREMOVE $RSYNCSOURCEFILENAME $FINALFILENAME

				LOGFILE=$TARGETDIR$SESSIONPATH
				LOGFILE+=transfer.log
				echo "LOGFILE IS $LOGFILE"
				echo "Compression and transfer of $FINALEFILENAME successful" >> $LOGFILE;
				chmod --reference=$FILEPATH$NEWFILE $FINALFILENAME;
				chown -v --reference=$FILEPATH$NEWFILE $FINALFILENAME;

				if [ -d "${FILEPATH}references" ]; then
					echo "######################"
					echo "RSYNC REFERENCES"
					echo rsync -av ${FILEPATH}references ${TARGETDIR}${SESSIONPATH}

					rsync -av --exclude=".*" ${FILEPATH}references ${TARGETDIR}${SESSIONPATH}
					echo "######################"
					wait $!; 
				fi
		 
			else
				echo skipping compression and rsync of $TARGETDIR$SESSIONPATH$j. 
			fi
		done

	fi
done
