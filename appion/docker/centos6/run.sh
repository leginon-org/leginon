#!/bin/sh

#  -v /Users/vosslab/myami/appion:/emg/sw/myami/appion \
#  -v /Users/vosslab/myami/pyami:/emg/sw/myami/pyami \
#  -v /Users/vosslab/myami/myamiweb/processing:/emg/sw/myami/myamiweb/processing \

docker run -d -t \
  -v /Users/vosslab/myami:/emg/sw/myami \
  -w /emg/sw/myami/appion \
  -p 80:80 -p 5901:5901 \
  vosslab/appion


