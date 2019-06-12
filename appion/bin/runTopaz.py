#!/usr/bin/env python

#!/usr/bin/env python
from subprocess import Popen, PIPE
import sys
command = ''.join(sys.argv[1:])
p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
output, err = p.communicate()
sys.stdout.write(output)

