The script needs to take three variables

1.  the output json file name without the extension
2.  input mrc file path
3.  the directory that contains the grid tile mrc file. This is redundant information, but is kept to give consistent 3 option input as the Hole Finding script

-   Within Leginon MosaicExternalScoreFinder instance defines, for each incoming gr image, a unique name from mosaic label and image id to form the value of variable 1.

Here is an example of this bash shell script we call sq_finding.sh

    #!/bin/sh -f
    #python3 /your_ptlomy/bin/runPtolemyLmm.py $1 $2 $3

    # This runs ptolemy locally using conda environment.
    source /usr/local/anaconda3/etc/profile.d/conda.sh
    conda activate /opt/condaenvs/ptolemy_env
    # variable 1 is the outputname without json extension
    # variable 2 is the input mrc path
    # variable 3 is the directory that contains the grid tile mrc file
    echo $1
    echo $2
    mrc_path=$2
    python/your/ptolemy/ptolemy/lowmag_cli.py -f json $2 > $1
    conda deactivate
    mv $1 ${mrc_path%%rawdata/*}rawdata/$1.json
    echo ${mrc_path%%rawdata/*}rawdata/$1.json

Test example, assuming you have /data/leginon/22feb28a/rawdata/22feb28a_00001gr.mrc, you can test ptolemy with

    ./sq_finding.sh test_1 /data/leginon/22feb28a/rawdata/22feb28a_00001gr.mrc dummy


Output test_1.json should end up in /data/leginon/22feb28a/rawdata/
