This shell script needs to take three arguments

1. output json rootname. Leginon will assign this according to the session name and node alias calling this. For example, "22mar15a_Exposure_Targeting"
2. full input mrc file path. Leginon will assign this according to its session path. For example "/data/leginon/22mar15a/rawdata/22mar15a_00001hl.mrc"
3. output directory name. Leginon will assign this to the directory where Leginon is launched, assuming write assess of the user. For example, "/home/your_name"

Here is an example script used at SEMC

    #!/bin/sh -f
    # Local runs
    source /usr/local/anaconda3/etc/profile.d/conda.sh
    conda activate /opt/condaenvs/ptolemy_env
    echo $1
    echo $2
    echo $3
    python /home/your_name/packages/ptolemy/medmag_cli.py -f json -o $3/$1.json $2
    conda deactivate

### Testing example

Assuming you have /data/leginon/22mar15a/rawdata/22mar15a_00001hl.mrc, and call the above script hl_finding.sh you can test with

    hl_finding.sh my_test /data/leginon/22mar15a/rawdata/22mar15a_00001hl.mrc .


You should get my_test.json written in your current directory.

During leginon operation, the output json will be read by Leginon into memory and be replaced each time it is run.

# Speeding up hole finding by running a holewatcher program

At NYU, we are running Ptolemy on a decently powered gpu workstation (2X Nvidia 1080, 128 GB RAM, 32 cores of Intel® Xeon® CPU E5-2683 v4 @ 2.10GHz). We found that hole finding was taking 12-14s. However, time could be cut in half by keeping ptolemy running all the time rather than running a new instance every time it was needed. We modified the holefinder to holewatcher.py, which runs all of the time and waits for a file to appear. LEginon runs the corresponding holemaker.sh program below. The only variable to change is outdir, which needs to match the target directory used by holewatcher.py. Time was reduced to 6-8s by doing this, and also by turning on CUDA in ptolemy.

    #!/bin/sh -f
    # changed for remote computer running a holewatcher program
    # wjr 10-13-22

    # modify outdir as needed to match that used by holewatcher.py
    outdir=/data/cryoem/cryoemdata/arctica_holes

    # sample output line 
    # 22oct13a_Exposure_Targeting /data/cryoem/cryoemdata/leginon/22oct13a/rawdata/22oct13a_p3b9g2a_00002sq_v01_00002hl.mrc /data/cryoem/cryoemdata/leginon/22oct13a/rawdata
    # the output file Leginon looks for is /data/cryoem/cryoemdata/leginon/22oct13a/rawdata/22oct13a_Exposure_Targeting.json

    echo $1 $2 $3 > $outdir/$1.txt

    # Leginon will look for the output immediately after this script ends, so this script needs a wait function
    mrc_path=$3
    file=$1
    slash='/'
    extension='.json'
    outfile=$mrc_path$slash$file$extension

    until [ -f $outfile ]
    do
         sleep 0.1
         echo waiting for $outfile
    done
    echo Got it
