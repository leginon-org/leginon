#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "usage: apache_mkdir.sh path user group (group optional)"
    exit
fi

if [ -z "$3" ]
  then
    mygrp=$2
else
  mygrp="$3"
fi

/usr/bin/su - $2 -c "/usr/bin/sg $mygrp -c '/bin/mkdir -p $1'"
