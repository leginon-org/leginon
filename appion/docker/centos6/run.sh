#!/bin/sh

docker run -d -t \
  -v /Users/vosslab/myami/appion:/emg/sw/myami/appion \
  -w /emg/sw/myami/appion \
  -p 80:80 -p 5901:5901 \
  vosslab/appion

