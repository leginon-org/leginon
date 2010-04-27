#!/bin/sh

echo "************** INC files ************** "
ls `find . -name '*.inc' -type f` | xargs -ir php -l r

sleep 5;

echo ""
echo ""
echo "************** PHP files ************** "
ls `find . -name '*.php' -type f` | xargs -ir php -l r

