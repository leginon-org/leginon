#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys
command = ' '.join(sys.argv[1:-4])
sys.stdout.write("Running: "+command)
p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
output, err = p.communicate()
if err:
    sys.stderr.write(err)
else:
    sys.stdout.write(output)

