#!/bin/sh

gource \
 --title "MyAMI Git History" \
 --hide filenames,mouse \
 --start-position 0.9 \
 --background 222222 \
 --font-size 18 \
 --fullscreen \
 --seconds-per-day 0.01 \
 --auto-skip-seconds 1 \
 --file-idle-time 60 \
 --bloom-multiplier 0.5 --bloom-intensity 0.25 \
 --output-framerate 25 \
 -o gource.ppm

