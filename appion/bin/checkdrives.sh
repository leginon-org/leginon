#!/bin/bash

for i in 00 01 02 06 07 08 09 10 11 12 13 14 15;
do
  cd /ami/data$i;
done;

df -h | sed 's/^Filesystem//' | sed 's/^ *//g' | egrep "(/ami/data|Size)" | sort -k 5
