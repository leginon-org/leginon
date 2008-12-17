#!/bin/sh
ls inc/*.inc | xargs -ir php -l r
ls *.php | xargs -ir php -l r
