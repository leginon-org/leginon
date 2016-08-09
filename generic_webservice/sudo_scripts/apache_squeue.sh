#!/bin/bash    

if [ "$#" -lt 1 ]; then
    echo "usage: apache_squeue.sh user "
    exit
fi


/usr/bin/su - $1 -c "/usr/bin/squeue -l -u $1"

