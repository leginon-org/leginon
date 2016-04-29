#!/bin/sh

docker run -d -t \
  -v /Users/vosslab/myami/appion:/emg/sw/myami/appion \
  -v /Users/vosslab/myami/myamiweb/processing:/emg/sw/myami/myamiweb/processing \
  -w /emg/sw/myami/appion \
  -p 80:80 -p 5901:5901 \
  vosslab/appion


