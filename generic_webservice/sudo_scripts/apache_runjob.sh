#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "usage: apache_runjob.sh \"runJob.py ctfestimate.py --runname=ctffindrun9.....\" user group (group is optional)"
    exit
fi

if [ -z "$3" ]
  then
    mygrp=$2
else
  mygrp="$3"
fi

/bin/su --login --group=$mygrp --shell="/bin/bash" --command="$1" $2